package server

import (
	"log"
	"net/http"
	"time"
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/gorilla/mux"
	"github.com/self-learning/backend/internal/config"
	"github.com/self-learning/backend/internal/database"
	"github.com/self-learning/backend/internal/handlers"
	"github.com/self-learning/backend/internal/ingestion"
	"github.com/self-learning/backend/internal/middleware"
	"github.com/self-learning/backend/internal/services"
	"gorm.io/gorm"
)

type Server struct {
	config    *config.Config
	db        *gorm.DB
	router    *mux.Router
	handlers  *handlers.Handler
	startTime time.Time
}

func New(cfg *config.Config) *Server {
	// 1. Initialize Database
	db := database.Connect(cfg.DatabasePath)

	// 2. Initialize services
	accountService := services.NewAccountService(db)

	// 3. Initialize handlers
	h := handlers.New(accountService)

	// 4. Start background workers
	queue := make(chan ingestion.SyncJob, 100)
	go ingestion.StartFetcherLoop(db, queue)
	go ingestion.StartNormalizerLoop(db, queue)

	log.Println("Background ingestion workers started")

	return &Server{
		config:    cfg,
		db:        db,
		handlers:  h,
		startTime: time.Now(),
	}
}


func (s *Server) Start() error {
	s.setupRoutes()

	// 1. Create a custom http.Server with timeouts (Critical for Security)
	srv := &http.Server{
		Addr:         ":" + s.config.Port,
		Handler:      s.router,
		ReadTimeout:  15 * time.Second,  // Max time to read the request body
		WriteTimeout: 15 * time.Second,  // Max time to write the response
		IdleTimeout:  60 * time.Second,  // Keep-alive connections
	}

	// 2. Run the server in a goroutine so it doesn't block the main thread
	serverErrors := make(chan error, 1)

	go func() {
		log.Printf("Server listening on port %s", s.config.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			serverErrors <- err
		}
	}()

	// 3. Listen for OS Signals (Graceful Shutdown)
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)

	// 4. Block until we receive a signal OR an error occurs
	select {
	case err := <-serverErrors:
		return fmt.Errorf("server error: %w", err)

	case <-shutdown:
		log.Println("🛑 Shutting down server...")

		// Create a context with a timeout (e.g., 5 seconds)
		// This tells the server: "Finish current requests, but you have 5s max."
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			// Force close if it takes too long
			srv.Close()
			return fmt.Errorf("could not stop server gracefully: %w", err)
		}
	}

	log.Println("✅ Server stopped gracefully")
	return nil
}

func (s *Server) setupRoutes() {
	s.router = mux.NewRouter()

	// 1. Global Middleware
	s.router.Use(middleware.CORS)
	s.router.Use(middleware.Recovery)

	// 2. Swagger Documentation
	// A. Serve the raw YAML spec (so the UI can read it)
	s.router.HandleFunc("/swagger.yaml", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "openapi.yaml")
	}).Methods("GET")

	// B. Serve the Swagger UI (HTML wrapper)
	s.router.HandleFunc("/swagger", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Budget App API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { display: none; } 
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
    <script>
        window.onload = () => {
            window.ui = SwaggerUIBundle({
                url: '/swagger.yaml',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
            });
        };
    </script>
</body>
</html>
		`))
	}).Methods("GET")

	// C. Root Redirect (User hits localhost:8080 -> goes to /swagger)
	s.router.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/swagger", http.StatusFound)
	}).Methods("GET")

	// 3. Health Check (Public - No Auth)
	s.router.HandleFunc("/health", s.handlers.HealthCheck).Methods("GET")

	// 4. API Routes (Protected)
	api := s.router.PathPrefix("/api/v1").Subrouter()

	// Apply JWT Auth Middleware
	// We pass s.db (to create users) and s.config.SupabaseURL (to fetch public keys)
	api.Use(middleware.JWTAuth(s.db, s.config.SupabaseURL))

	// Account Endpoints
	api.HandleFunc("/accounts", s.handlers.GetUserAccounts).Methods("GET")
	api.HandleFunc("/accounts/{accountID}/transactions", s.handlers.GetAccountTransactions).Methods("GET")
}