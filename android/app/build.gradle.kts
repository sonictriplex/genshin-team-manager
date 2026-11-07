plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "de.sonictriplex.genshinteams"
    compileSdk = 37

    defaultConfig {
        applicationId = "de.sonictriplex.genshinteams"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    buildFeatures {
        compose = true
    }

    // Gemeinsame Daten des Monorepos (Bilder, Schrift, Stammdaten) direkt als Assets einbinden.
    // Unter assets/ liegen sie dann wie im Repo: assets/images/<name>.png, stammdaten.json
    sourceSets["main"].assets.directories.add("../../shared")
    // Spezifikation und Testdaten gehören nicht in die APK
    androidResources.ignoreAssetsPatterns.addAll(listOf("!testdata", "!*.md", "!*.schema.json"))

    testOptions {
        unitTests.all {
            // Tests lesen Referenzdateien aus shared/ (relativ zum Modulordner)
            it.systemProperty("shared.dir", file("../../shared").absolutePath)
        }
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.okhttp)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)
    debugImplementation(libs.androidx.compose.ui.tooling)

    testImplementation(libs.junit)
}
