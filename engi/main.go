package main

import (
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
)

const SHIKI_API_URL = "http://localhost:8000"
const ENGI_PORT = ":8080"

func main() {
	url, err := url.Parse(SHIKI_API_URL)
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

	log.Printf("Starting Engi proxy on port %s, forwarding to %s", ENGI_PORT, SHIKI_API_URL)

	http.HandleFunc("/", proxy.ServeHTTP)

	if err := http.ListenAndServe(ENGI_PORT, nil); err != nil {
		panic(err)
	}
}
