package com.asanda.structuralpro
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity: ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { StructuralProHome() }
    }
}
@Composable
fun StructuralProHome() {
    var screen by remember { mutableStateOf("داشبورد") }
    MaterialTheme {
        Column(Modifier.fillMaxSize().padding(20.dp)) {
            Text("StructuralPro", style=MaterialTheme.typography.headlineMedium)
            Text("Offline-first • پروژه‌ها و متره")
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                Button(onClick={screen="پروژه‌ها"}) { Text("پروژه‌ها") }
                Button(onClick={screen="متره"}) { Text("متره") }
                Button(onClick={screen="تنظیمات"}) { Text("تنظیمات") }
            }
            Spacer(Modifier.height(20.dp))
            Text(screen, style=MaterialTheme.typography.titleLarge)
            Text(if(screen=="متره") "ورود سریع متره؛ موتور مهندسی در هسته مشترک پروژه اجرا می‌شود." else "نسخه Android از همان قرارداد پروژه استفاده می‌کند.")
        }
    }
}
