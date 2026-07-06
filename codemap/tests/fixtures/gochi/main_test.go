// ABOUTME: Test fixture — routes declared in a _test.go must NOT appear in the map
// ABOUTME: Also exercises the Header.Get false-positive shape (single argument)

package main

func testRoutes(r Router) {
	r.Get("/should-not-appear", noopHandler)
	_ = r.Header.Get("Content-Type")
}
