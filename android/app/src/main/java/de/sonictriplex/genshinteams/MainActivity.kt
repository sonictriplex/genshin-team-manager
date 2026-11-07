package de.sonictriplex.genshinteams

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import de.sonictriplex.genshinteams.ui.AppViewModel
import de.sonictriplex.genshinteams.ui.BuildScreen
import de.sonictriplex.genshinteams.ui.EditBuildScreen
import de.sonictriplex.genshinteams.ui.EditTeamScreen
import de.sonictriplex.genshinteams.ui.GenshinTheme
import de.sonictriplex.genshinteams.ui.LoginScreen
import de.sonictriplex.genshinteams.ui.TeamsScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            GenshinTheme {
                Surface(Modifier.fillMaxSize()) { App() }
            }
        }
    }
}

@Composable
private fun App(vm: AppViewModel = viewModel()) {
    val nav = rememberNavController()

    // Beim Start mit gespeicherter Anmeldung die Daten laden
    LaunchedEffect(Unit) { if (vm.loggedIn && vm.userData == null) vm.refresh() }

    if (!vm.loggedIn) {
        LoginScreen(vm)
        return
    }

    NavHost(nav, startDestination = "teams") {
        composable("teams") {
            TeamsScreen(
                vm,
                onOpenCharacter = { nav.navigate("character/${Uri.encode(it)}") },
                onNewTeam = { nav.navigate("team/new") },
                onEditTeam = { nav.navigate("team/edit/${Uri.encode(it)}") },
            )
        }
        composable("team/new") { EditTeamScreen(vm, originalName = null, onDone = { nav.popBackStack() }) }
        composable("team/edit/{name}") { entry ->
            EditTeamScreen(vm, entry.arguments?.getString("name").orEmpty(), onDone = { nav.popBackStack() })
        }
        composable("character/{name}") { entry ->
            val name = entry.arguments?.getString("name").orEmpty()
            BuildScreen(vm, name, onBack = { nav.popBackStack() }, onEdit = { nav.navigate("character/${Uri.encode(name)}/edit") })
        }
        composable("character/{name}/edit") { entry ->
            val name = entry.arguments?.getString("name").orEmpty()
            EditBuildScreen(vm, name, onDone = { nav.popBackStack() })
        }
    }
}
