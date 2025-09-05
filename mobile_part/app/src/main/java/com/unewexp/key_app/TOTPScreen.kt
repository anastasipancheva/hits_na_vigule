package com.unewexp.key_app

import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.unewexp.key_app.ui.theme.Typography
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

@Composable
fun TotpScreen(
    secret: ByteArray,
    onBackPress: () -> Unit
){
    BackHandler {
        onBackPress()
    }
    if (secret.isEmpty()){
        onBackPress()
        Toast.makeText(LocalContext.current, "Отсутствует ключ", Toast.LENGTH_SHORT).show();
    }
    val totpGenerator = TotpGenerator()
    var totp by remember { mutableStateOf("") }
    var progress by remember { mutableStateOf(0f) }

    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        animationSpec = tween(durationMillis = 1000),
        label = "progressAnimation"
    )

    LaunchedEffect(secret) {
        while (true) {
            val newTotp = withContext(Dispatchers.IO) {
                totpGenerator.generateTotpCode(secret)
            }
            val newProgress = withContext(Dispatchers.IO) {
                totpGenerator.getProgress()
            }
            totp = newTotp
            progress = newProgress.toFloat()/100f
            delay(100L)
        }
    }

    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box{
            Text(totp, style = Typography.titleMedium.copy(fontSize = 40.sp))
        }
        Spacer(Modifier.height(30.dp))

        LinearProgressIndicator(
            progress = { 1.0f - animatedProgress },
            modifier = Modifier.height(10.dp),
            color = Color(233, 89, 20)
        )
    }
}