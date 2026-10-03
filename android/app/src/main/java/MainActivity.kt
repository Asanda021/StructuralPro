package com.asanda.structuralpro

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val view = TextView(this)
        view.text = "StructuralPro"
        view.textSize = 24f
        view.textDirection = TextView.TEXT_DIRECTION_RTL
        setContentView(view)
    }
}
