// ABOUTME: Test fixture — chi router with chained middleware and net/http registration
// ABOUTME: Exercises the go-routes rule: Get/Post/Mount/Route/HandleFunc, variable paths

package main

import "net/http"

func routes(r Router, configPath string) {
	r.Get("/health", healthHandler)
	r.With(rbac("read")).Get(configPath, getConfig)
	r.Post(configPath+"/test", testConnection)
	r.Mount("/v1", apiRouter())
	r.Route("/admin", adminRoutes)
	r.Route("/audit", func(r Router) {
		r.Get("/", listAudit)
		r.Post("/export", exportAudit)
	})
	http.HandleFunc("/metrics", metricsHandler)
	r.Post("/long", makeVeryLongHandlerName(withSomeConfig, andMoreConfig, andEvenMoreConfigForGoodMeasure))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {}
