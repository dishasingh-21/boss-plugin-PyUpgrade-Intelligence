package ai.rever.boss.plugin.dynamic.pyupgradeIntelligence
import ai.rever.boss.plugin.api.McpToolResult
import java.io.File

internal class PythonEngineBridge {
    private val enginePath: String = System.getenv("PYUPGRADE_ENGINE_PATH")
        ?: findDefaultEnginePath()
        ?: throw IllegalStateException(
            "Could not locate the PyUpgrade Intelligence Python engine. Set the PYUPGRADE_ENGINE_PATH " +
            "environment variable to the absolute path of the 'engine' folder, or place it " +
            "at the documented default location. See the README for setup instructions."
        )

    fun runCommand(args: List<String>): McpToolResult {
        val pythonExe = resolvePythonExecutable()
        val fullCommand = listOf(pythonExe, "$enginePath/cli.py") + args

        val process = ProcessBuilder(fullCommand)
            .directory(File(enginePath))
            .redirectErrorStream(true)
            .start()

        val output = process.inputStream.bufferedReader().readText()
        val exitCode = process.waitFor()

        return if (exitCode == 0) {
            McpToolResult(output)
        } else {
            McpToolResult(output, isError = true)
        }
    }

    private fun resolvePythonExecutable(): String {
        val venvPython = File("$enginePath/.venv/Scripts/python.exe")
        return if (venvPython.exists()) venvPython.absolutePath else "python"
    }

    private fun findDefaultEnginePath(): String? {
        val jarLocation = File(
            PythonEngineBridge::class.java.protectionDomain.codeSource.location.toURI()
        )
        val repoRoot = jarLocation.parentFile?.parentFile?.parentFile
        val candidate = File(repoRoot, "engine")
        return if (candidate.exists()) candidate.absolutePath else null
    }
}