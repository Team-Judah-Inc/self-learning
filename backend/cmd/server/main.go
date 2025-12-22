package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/mux"
	"github.com/self-learning/backend/cmd/auth"
	"github.com/self-learning/backend/internal/database"
	"github.com/self-learning/backend/internal/ingestion"
)

func main() {
	// 1. Initialize Database
	db := database.Connect("riseapp.db")

	// 2. Create the internal Queue (Buffered Channel)
	// This acts as the "Queue" between Fetcher and Normalizer
	queue := make(chan ingestion.SyncJob, 100)

	// 3. Start the Background Fetcher (The Engine)
	go ingestion.StartFetcherLoop(db, queue)

	// 4. Start the Real Normalizer (The Chef - Loop B)
	go ingestion.StartNormalizerLoop(db, queue)

	// 5. Start HTTP Server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	router := mux.NewRouter()
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"alive"}`))
	})

	log.Printf("Server starting on port %s", port)
	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal(err)
	}
}
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status":"healthy"}`)
}
func rootHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"message":"Welcome to Self-Learning Protected API"}`)
}
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}
func MiddleBasicAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		username, password, ok := r.BasicAuth()
		fmt.Println("MiddleBasicAuth")
		if ok {
			if auth.BasicAuth(auth.User{
				Username: username,
				Password: password,
			}) {
				fmt.Println("User successfully authenticated")
				next.ServeHTTP(w, r)
			} else {
				fmt.Println("User authentication failed")
				w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
			}
		}
	})

}
