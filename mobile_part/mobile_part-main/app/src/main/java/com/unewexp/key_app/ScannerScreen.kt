package com.unewexp.key_app

import android.Manifest
import android.content.pm.PackageManager
import android.view.ViewGroup
import androidx.activity.compose.BackHandler
import androidx.annotation.OptIn
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

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