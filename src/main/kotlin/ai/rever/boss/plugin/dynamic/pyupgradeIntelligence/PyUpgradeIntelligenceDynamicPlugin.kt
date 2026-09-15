package ai.rever.boss.plugin.dynamic.pyupgradeIntelligence

import ai.rever.boss.plugin.api.DynamicPlugin
import ai.rever.boss.plugin.api.PluginContext

class PyUpgradeIntelligenceDynamicPlugin : DynamicPlugin {
    override val pluginId = "ai.rever.boss.plugin.dynamic.pyupgrade_intelligence"
    override val displayName = "PyUpgrade Intelligence"
    override val version = "0.1.0"
    override val description = "Semantic graph-based upgrade risk checker for Python frameworks"
    override val author = "Disha Singh"
    override val url = "https://github.com/dishasingh-21/boss-plugin-PyUpgrade-Intelligence"

    override fun register(context: PluginContext) {
        val engine = PythonEngineBridge()
        context.registerMcpToolProvider(PyUpgradeMcpToolProvider(pluginId, engine))
    }

    override fun dispose() {
        // Release any resources here (the host calls this on unload).
    }
}
