package main

import (
	"flag"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"

	"github.com/BurntSushi/toml"
)

type Config struct {
	Engi  EngiConfig  `toml:"engi"`
	Shiki ShikiConfig `toml:"shiki"`
}

type EngiConfig struct {
	Host string `toml:"host"`
	Port int    `toml:"port"`
}

type ShikiConfig struct {
	Host string `toml:"host"`
	Port int    `toml:"port"`
}

func loadConfig(path string) (*Config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg Config
	if err := toml.Unmarshal(b, &cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}

func main() {
	// flags
	cfgPath := flag.String("config", "", "Path to config file")
	flag.Parse()

	// load config
	cfg, err := loadConfig(*cfgPath)
	if err != nil {
		panic(err)
	}

	shikiUrl := cfg.Shiki.Host + ":" + strconv.Itoa(cfg.Shiki.Port)
	engiUrl := cfg.Engi.Host + ":" + strconv.Itoa(cfg.Engi.Port)

	url, err := url.Parse(shikiUrl)
	if err != nil {
		panic(err)
	}

	proxy := httputil.NewSingleHostReverseProxy(url)
	proxy.Director = func(req *http.Request) {
		req.URL.Scheme = url.Scheme
		req.URL.Host = url.Host
		req.Host = url.Host

		log.Printf("Transporting request: %s %s", req.Method, req.URL.Path)
	}

	log.Printf("Starting Engi proxy on port %s, forwarding to %s", engiUrl, shikiUrl)

	http.HandleFunc("/", proxy.ServeHTTP)

	if err := http.ListenAndServe(engiUrl, nil); err != nil {
		panic(err)
	}
}
