package com.unewexp.key_app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.OptIn
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.unewexp.key_app.ui.theme.Key_AppTheme
import com.unewexp.key_app.ui.theme.Typography
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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
            Column {
                Button(
                    onClick = {
                        isMainScreen = false
                        isScannerScreen = true
                    }
                ) {
                    Text("Сканирование")
                }

                Spacer(
                    modifier = Modifier.height(20.dp)
                )

                Button(
                    onClick = {
                        isMainScreen = false
                        isScannerScreen = false
                    }
                ) {
                    Text("Генерация кода")
                }
            }
        }
    }else if(isScannerScreen){
        ScannerScreen(
            ScanType.ScanQr,
            { it ->
                dataStore.savePassword("secret", it)
                val value = dataStore.getPassword("secret")
                if (value != null){
                    Log.i("asdd", value)
                }
                isMainScreen = true
            },
            {
                isMainScreen = true
                isScannerScreen = false
            }
        )
    }else{
        val secret = dataStore.getPassword("secret")
        if(secret != null){
            TotpScreen(
                secret = secret.toByteArray(),
                {
                    isMainScreen = true
                }
            )
        }
    }
}

@OptIn(ExperimentalGetImage::class)
@Composable
fun ScannerScreen(
    scanType: ScanType,
    onCodeScanned: ((String) -> Unit)? = null,
    onBackPress: (() -> Unit)
) {
    BackHandler {
        onBackPress()
    }
    val lifecycleOwner = LocalLifecycleOwner.current
    val context = LocalContext.current
    val analysisExecutor = remember { CoroutineScope(Dispatchers.Default) }
    val cameraProviderFuture = remember { ProcessCameraProvider.getInstance(context) }

    DisposableEffect(Unit) {
        onDispose {
            val cameraProvider = cameraProviderFuture.get()
            cameraProvider.unbindAll()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        AndroidView(
            factory = { ctx ->
                val previewView = PreviewView(ctx).apply {
                    layoutParams = ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    scaleType = PreviewView.ScaleType.FILL_CENTER
                }
                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()

                    val previewUseCase = Preview.Builder().build().also {
                        it.surfaceProvider = previewView.surfaceProvider
                    }

                    val permissionGranted = ContextCompat.checkSelfPermission(
                        ctx, Manifest.permission.CAMERA
                    ) == PackageManager.PERMISSION_GRANTED

                    val barcodeScanner = BarcodeScanning.getClient(
                        BarcodeScannerOptions.Builder()
                            .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                            .build()
                    )

                    if (!permissionGranted) {
                        return@addListener
                    }

                    val selector = when {
                        cameraProvider.hasCamera(CameraSelector.DEFAULT_BACK_CAMERA) -> CameraSelector.DEFAULT_BACK_CAMERA
                        cameraProvider.hasCamera(CameraSelector.DEFAULT_FRONT_CAMERA) -> CameraSelector.DEFAULT_FRONT_CAMERA
                        else -> {
                            return@addListener
                        }
                    }

                    val analysisUseCase = ImageAnalysis.Builder()
                        .setTargetResolution(android.util.Size(1280, 720))
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build()
                        .also { analysis ->
                            analysis.setAnalyzer(
                                { runnable -> analysisExecutor.launch { runnable.run() } }
                            ) { imageProxy ->
                                val mediaImage = imageProxy.image

                                if (mediaImage != null) {
                                    val rotation = imageProxy.imageInfo.rotationDegrees
                                    val inputImage = InputImage.fromMediaImage(mediaImage, rotation)
                                    when (scanType) {
                                        ScanType.ScanQr -> {
                                            barcodeScanner.process(inputImage)
                                                .addOnSuccessListener { barcodes ->
                                                    barcodes.firstOrNull { barcode ->
                                                        val box = barcode.boundingBox
                                                        box != null
                                                    }?.rawValue?.let { qrCode ->
                                                        onCodeScanned?.let { it(qrCode) }
                                                    }
                                                }
                                                .addOnCompleteListener {
                                                    imageProxy.close()
                                                }
                                        }

                                        ScanType.None -> {}
                                    }
                                } else {
                                    imageProxy.close()
                                }
                            }
                        }

                    try {
                        cameraProvider.unbindAll()
                        cameraProvider.bindToLifecycle(
                            lifecycleOwner,
                            selector,
                            previewUseCase,
                            analysisUseCase
                        )
                    } catch (exception: Exception) {
                    }

                }, ContextCompat.getMainExecutor(ctx))

                previewView
            },
            modifier = Modifier.fillMaxSize()
        )
        when (scanType) {

            ScanType.ScanQr -> { /*CameraScanQrOverlay()*/ }

            ScanType.None -> {}
        }
    }
}


sealed class ScanType() {
    data object ScanQr: ScanType()
    data object None: ScanType()
}

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
            modifier = Modifier.height(10.dp)
        )
    }
}