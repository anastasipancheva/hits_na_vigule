package com.unewexp.key_app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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
import com.unewexp.key_app.ui.theme.Key_AppTheme
import com.unewexp.key_app.ui.theme.Typography
import org.apache.commons.codec.binary.Base32

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()


        setContent {
            Key_AppTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    MainScreen(paddingValues = innerPadding)
                }
            }
        }
    }
}

@Composable
fun MainScreen(paddingValues: PaddingValues){

    val dataStore = SecureDataStore(LocalContext.current)
    var isMainScreen by remember { mutableStateOf(true) }
    var isScannerScreen by remember { mutableStateOf(false) }

    if (isMainScreen) {
        Box(
            modifier = Modifier.fillMaxSize().padding(paddingValues),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Button(
                    onClick = {
                        isMainScreen = false
                        isScannerScreen = true
                    },
                    shape = RoundedCornerShape(20),
                    colors = ButtonDefaults.buttonColors().copy(
                        containerColor = Color(255,255,255),
                        contentColor = Color(248,116,28)
                    ),
                    border = BorderStroke(2.dp, Color(248,116,28)),
                    modifier = Modifier.fillMaxHeight(0.07f).fillMaxWidth(0.7f)
                ) {
                    Text("Сканирование", style = Typography.bodyMedium.copy(fontSize = 14.sp))
                }

                Spacer(
                    modifier = Modifier.height(30.dp)
                )

                Button(
                    onClick = {
                        isMainScreen = false
                        isScannerScreen = false
                    },
                    colors = ButtonDefaults.buttonColors().copy(
                        containerColor = Color(233,89,20),
                        contentColor = Color(255,255,255)
                    ),
                    shape = RoundedCornerShape(20),
                    border = BorderStroke(2.dp, Color(233,89,20)),
                    modifier = Modifier.fillMaxHeight(0.07f).fillMaxWidth(0.7f)
                ) {
                    Text("Генерация кода", style = Typography.bodyMedium.copy(fontSize = 14.sp))
                }
            }
        }
    }else if(isScannerScreen){
        ScannerScreen(
            ScanType.ScanQr,
            { it ->
                dataStore.savePassword("secret", it)
                isMainScreen = true
            },
            {
                isMainScreen = true
                isScannerScreen = false
            }
        )
    }else{
        val secret = dataStore.getPassword("secret")
        val base32 = Base32()
        val secretBytes = base32.decode(secret)
        if(secret != null){
            TotpScreen(
                secret = secretBytes
            ) {
                isMainScreen = true
            }
        }
    }
}