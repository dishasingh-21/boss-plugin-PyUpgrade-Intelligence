import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.3.0"
}

group = "ai.rever.boss.plugin.dynamic"
version = "0.1.0"

java {
    toolchain { languageVersion.set(JavaLanguageVersion.of(17)) }
}
kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

val useLocalDependencies = System.getenv("CI") != "true"
val bossPluginApiPath = "../boss-plugin-api"

repositories {
    mavenCentral()
}

dependencies {
    if (useLocalDependencies) {
        compileOnly(files("$bossPluginApiPath/build/libs/boss-plugin-api-1.0.93.jar"))
    } else {
        compileOnly(files("build/downloaded-deps/boss-plugin-api.jar"))
    }
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
}

tasks.register<Jar>("buildPluginJar") {
    archiveFileName.set("boss-plugin-pyupgrade-intelligence-${version}.jar")
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    manifest {
        attributes(
            "Implementation-Title" to "PyUpgrade Intelligence",
            "Implementation-Version" to version,
            "Main-Class" to "ai.rever.boss.plugin.dynamic.pyupgrade_intelligence.PyUpgradeIntelligenceDynamicPlugin",
        )
    }
    from(sourceSets.main.get().output)
    from("src/main/resources")
}

tasks.processResources {
    filesMatching("**/plugin.json") {
        filter { line ->
            line.replace(Regex(""""version"\s*:\s*"[^"]*""""), """"version": "$version"""")
        }
    }
}

tasks.build { dependsOn("buildPluginJar") }