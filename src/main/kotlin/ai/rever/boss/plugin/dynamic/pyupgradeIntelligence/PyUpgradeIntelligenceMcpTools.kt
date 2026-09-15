package ai.rever.boss.plugin.dynamic.pyupgradeIntelligence
import ai.rever.boss.plugin.api.McpToolDefinition
import ai.rever.boss.plugin.api.McpToolHandler
import ai.rever.boss.plugin.api.McpToolProvider
import ai.rever.boss.plugin.api.McpToolResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

internal class PyUpgradeMcpToolProvider(override val providerId: String, private val engine: PythonEngineBridge) : McpToolProvider {
    override fun tools(): List<McpToolDefinition> = listOf(
        McpToolDefinition(
            name = "pyupgrade_check",
            description = "Check the risk of upgrading a Python framework from one version to " +
                "another, for a specific codebase. Returns a compact risk score (0-100), a " +
                "recommendation, the specific symbol driving the score, and affected files. " +
                "If this is the first time checking this framework/version pair, call " +
                "pyupgrade_warm_cache for both versions first to avoid a slow first-time build " +
                "inside this call.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"versionFrom":{"type":"string"},"versionTo":{"type":"string"},"repoPath":{"type":"string"}},"required":["framework","versionFrom","versionTo","repoPath"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val versionFrom = args.string("versionFrom") ?: return@withContext McpToolResult("Missing required argument: versionFrom", isError = true)
                    val versionTo = args.string("versionTo") ?: return@withContext McpToolResult("Missing required argument: versionTo", isError = true)
                    val repoPath = args.string("repoPath") ?: return@withContext McpToolResult("Missing required argument: repoPath", isError = true)
                    engine.runCommand(listOf("check", framework, versionFrom, versionTo, "--repo", repoPath))
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_warm_cache",
            description = "Pre-builds and caches a framework version's semantic graph without " +
                "running a full check. Call this FIRST, once per version, before pyupgrade_check " +
                "or pyupgrade_get_breaking_changes on a framework/version pair not yet checked " +
                "this session, avoids the first-time build cost landing inside a time-limited call.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"version":{"type":"string"},"packageName":{"type":"string"}},"required":["framework","version"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val version = args.string("version") ?: return@withContext McpToolResult("Missing required argument: version", isError = true)
                    val packageName = args.string("packageName")
                    val cmd = mutableListOf("warm", framework, version)
                    if (packageName != null) { cmd += "--package"; cmd += packageName }
                    engine.runCommand(cmd)
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_get_breaking_changes",
            description = "Get the structural diff between two framework versions, without " +
                "cross-referencing any specific codebase. Returns high-confidence changes " +
                "(removed symbols, signature changes, moves) by default.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"versionFrom":{"type":"string"},"versionTo":{"type":"string"}},"required":["framework","versionFrom","versionTo"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val versionFrom = args.string("versionFrom") ?: return@withContext McpToolResult("Missing required argument: versionFrom", isError = true)
                    val versionTo = args.string("versionTo") ?: return@withContext McpToolResult("Missing required argument: versionTo", isError = true)
                    engine.runCommand(listOf("changes", framework, versionFrom, versionTo))
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_get_usage",
            description = "List every framework symbol a codebase uses, with file and line for " +
                "each usage independent of any version comparison.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"version":{"type":"string"},"repoPath":{"type":"string"}},"required":["framework","version","repoPath"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val version = args.string("version") ?: return@withContext McpToolResult("Missing required argument: version", isError = true)
                    val repoPath = args.string("repoPath") ?: return@withContext McpToolResult("Missing required argument: repoPath", isError = true)
                    engine.runCommand(listOf("usage", framework, version, "--repo", repoPath))
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_get_affected_files",
            description = "Get the specific files and lines in a codebase affected by changes " +
                "between two framework versions.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"versionFrom":{"type":"string"},"versionTo":{"type":"string"},"repoPath":{"type":"string"},"enriched":{"type":"boolean"}},"required":["framework","versionFrom","versionTo","repoPath"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val versionFrom = args.string("versionFrom") ?: return@withContext McpToolResult("Missing required argument: versionFrom", isError = true)
                    val versionTo = args.string("versionTo") ?: return@withContext McpToolResult("Missing required argument: versionTo", isError = true)
                    val repoPath = args.string("repoPath") ?: return@withContext McpToolResult("Missing required argument: repoPath", isError = true)
                    val enriched = args.boolean("enriched") ?: false
                    val cmd = mutableListOf("affected", framework, versionFrom, versionTo, "--repo", repoPath)
                    if (enriched) cmd += "--enriched"
                    engine.runCommand(cmd)
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_get_config_diff",
            description = "Get the plain-text diff of config/dependency files (pyproject.toml, " +
                "setup.cfg, requirements.txt) between two framework versions.",
            inputSchema = """{"type":"object","properties":{"framework":{"type":"string"},"versionFrom":{"type":"string"},"versionTo":{"type":"string"}},"required":["framework","versionFrom","versionTo"]}""",
            handler = McpToolHandler { args ->
                withContext(Dispatchers.IO) {
                    val framework = args.string("framework") ?: return@withContext McpToolResult("Missing required argument: framework", isError = true)
                    val versionFrom = args.string("versionFrom") ?: return@withContext McpToolResult("Missing required argument: versionFrom", isError = true)
                    val versionTo = args.string("versionTo") ?: return@withContext McpToolResult("Missing required argument: versionTo", isError = true)
                    engine.runCommand(listOf("config-diff", framework, versionFrom, versionTo))
                }
            },
        ),
        McpToolDefinition(
            name = "pyupgrade_list_cached_frameworks",
            description = "List every framework version whose semantic graph is already built " +
                "and cached locally.",
            handler = McpToolHandler {
                withContext(Dispatchers.IO) {
                    engine.runCommand(listOf("cache", "list"))
                }
            },
        ),
    )
}