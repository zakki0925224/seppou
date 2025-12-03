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
	Host          string `toml:"host"`
	Port          int    `toml:"port"`
	MaxReqsPerSec int    `toml:"max_reqs_per_sec"`
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

	// limiter
	limiter := NewRateLimiter(cfg.Engi.MaxReqsPerSec)

	handler := http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		if !limiter.Allow() {
			log.Printf("Rate limit exceeded for request: %s %s", req.Method, req.URL.Path)
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		log.Printf("Transporting request: %s %s", req.Method, req.URL.Path)
		proxy.ServeHTTP(w, req)
	})

	log.Printf("Starting Engi proxy on %s, forwarding to %s", engiUrl, shikiUrl)

	if err := http.ListenAndServe(engiUrl, handler); err != nil {
		panic(err)
	}
}
