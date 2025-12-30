package server

import (
	"log"
	"net/http"
	"time"

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
	return http.ListenAndServe(":"+s.config.Port, s.router)
}

func (s *Server) setupRoutes() {
	s.router = mux.NewRouter()

	// Global middleware
	s.router.Use(middleware.CORS)
	s.router.Use(middleware.Recovery)

	// Health check (no auth required)
	s.router.HandleFunc("/health", s.handlers.HealthCheck).Methods("GET")

	// API routes with Basic Auth protection
	api := s.router.PathPrefix("/api/v1").Subrouter()

	// Apply Basic Auth middleware to all API routes
	api.Use(middleware.BasicAuth)
	
	// Account routes
	api.HandleFunc("/accounts", s.handlers.GetUserAccounts).Methods("GET")
}
