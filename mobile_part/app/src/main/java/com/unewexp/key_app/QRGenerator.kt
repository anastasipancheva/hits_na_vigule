package com.unewexp.key_app

import android.graphics.Bitmap
import androidx.core.graphics.createBitmap
import com.google.zxing.BarcodeFormat
import com.google.zxing.WriterException
import com.journeyapps.barcodescanner.BarcodeEncoder


fun generateQRCode(text: String?): Bitmap {
    val barcodeEncoder = BarcodeEncoder()
    try {

        val bitmap = barcodeEncoder.encodeBitmap(text, BarcodeFormat.QR_CODE, 800, 800)

        return bitmap
    } catch (e: WriterException) {
        e.printStackTrace()
    }
    return createBitmap(400, 400)
}