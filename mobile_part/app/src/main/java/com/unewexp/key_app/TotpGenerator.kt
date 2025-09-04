package com.unewexp.key_app

import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class TotpGenerator() {

    fun generateTotpCode(secretKey: ByteArray): String {
        val timeStep = 30L
        val digits = 6

        val currentTime = System.currentTimeMillis() / 1000
        val counter = currentTime / timeStep

        return generateHotp(secretKey, counter, digits)
    }

    private fun generateHotp(secret: ByteArray, counter: Long, digits: Int): String {
        var counter = counter
        val text = ByteArray(8)
        for (i in 7 downTo 0) {
            text[i] = (counter and 0xff).toByte()
            counter = counter shr 8
        }

        val keySpec = SecretKeySpec(secret, "HmacSHA1")
        val mac = Mac.getInstance("HmacSHA1")
        mac.init(keySpec)
        val hash = mac.doFinal(text)

        val offset = hash[hash.size - 1].toInt() and 0xf
        val binary = ((hash[offset].toInt() and 0x7f) shl 24) or
                ((hash[offset + 1].toInt() and 0xff) shl 16) or
                ((hash[offset + 2].toInt() and 0xff) shl 8) or
                (hash[offset + 3].toInt() and 0xff)

        val otp = binary % Math.pow(10.0, digits.toDouble()).toInt()
        return otp.toString().padStart(digits, '0')
    }

    fun getProgress(): Int {
        val timeStep = 30L
        val currentTime = System.currentTimeMillis() / 1000
        val timeRemaining = timeStep - (currentTime % timeStep)
        return ((timeStep - timeRemaining) * 100 / timeStep).toInt()
    }
}