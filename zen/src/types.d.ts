interface ShikiConfig {
    host: string;
    port: number;
}

interface ZenConfig {
    polling_interval_ms: number;
}

declare module "../../config.toml" {
    const config: {
        shiki: ShikiConfig;
        zen: ZenConfig;
    };
    export default config;
}
