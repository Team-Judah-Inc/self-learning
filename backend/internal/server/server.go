package server

import (
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/self-learning/backend/internal/config"
	"github.com/self-learning/backend/internal/handlers"
	"github.com/self-learning/backend/internal/middleware"
)

type Server struct {
	config    *config.Config
	router    *mux.Router
	handlers  *handlers.Handler
	startTime time.Time
}

func New(cfg *config.Config) *Server {
	// Initialize services
	//authService := services.NewAuthService(userRepo, cfg.JWTSecret)

	// Initialize handlers
	h := handlers.New()
	return &Server{
		config:    cfg,
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
	
}
