# Clara Infrastructure - Makefile
# Quick commands for managing Docker infrastructure

.PHONY: help start stop restart logs status clean backup

# Default target
help:
	@echo "Clara Infrastructure Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (copy .env and start services)"
	@echo "  make start          - Start all infrastructure services"
	@echo "  make start-tools    - Start with management tools (Redis Commander, pgAdmin)"
	@echo ""
	@echo "Management:"
	@echo "  make stop           - Stop all services (keeps data)"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make status         - Check service status"
	@echo ""
	@echo "Individual Services:"
	@echo "  make redis          - Start only Redis"
	@echo "  make postgres       - Start only PostgreSQL"
	@echo "  make timescale      - Start only TimescaleDB"
	@echo ""
	@echo "Database Access:"
	@echo "  make redis-cli      - Connect to Redis CLI"
	@echo "  make psql           - Connect to PostgreSQL"
	@echo "  make psql-analytics - Connect to TimescaleDB"
	@echo ""
	@echo "Maintenance:"
	@echo "  make backup         - Backup all databases"
	@echo "  make clean          - Stop and remove containers (keeps data)"
	@echo "  make clean-all      - ⚠️  Remove everything including data"
	@echo "  make reset          - ⚠️  Reset all data and restart fresh"
	@echo ""

# Setup
setup:
	@echo "📦 Setting up Clara infrastructure..."
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "✅ Created .env file from .env.docker"; \
	else \
		echo "⚠️  .env already exists, skipping copy"; \
	fi
	@echo "🚀 Starting services..."
	@docker-compose up -d
	@echo "✅ Setup complete! Run 'make status' to check services."

# Start services
start:
	@echo "🚀 Starting Clara infrastructure..."
	@docker-compose up -d
	@echo "✅ Services started. Run 'make status' to check."

start-tools:
	@echo "🚀 Starting Clara infrastructure with management tools..."
	@docker-compose --profile tools up -d
	@echo "✅ Services started."
	@echo ""
	@echo "🔗 Management UIs:"
	@echo "   Redis Commander: http://localhost:8081"
	@echo "   pgAdmin:         http://localhost:5050 (admin@clara.local / admin)"

# Individual services
redis:
	@docker-compose up -d redis
	@echo "✅ Redis started on port 6379"

postgres:
	@docker-compose up -d postgres
	@echo "✅ PostgreSQL started on port 5432"

timescale:
	@docker-compose up -d timescaledb
	@echo "✅ TimescaleDB started on port 5433"

# Stop/Restart
stop:
	@echo "🛑 Stopping services..."
	@docker-compose stop
	@echo "✅ Services stopped (data preserved)"

restart:
	@echo "🔄 Restarting services..."
	@docker-compose restart
	@echo "✅ Services restarted"

# Logs and Status
logs:
	@docker-compose logs -f

logs-redis:
	@docker-compose logs -f redis

logs-postgres:
	@docker-compose logs -f postgres

logs-timescale:
	@docker-compose logs -f timescaledb

status:
	@echo "📊 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "💾 Volume Usage:"
	@docker volume ls | grep clara || echo "No Clara volumes found"

# Database CLI access
redis-cli:
	@docker-compose exec redis redis-cli

psql:
	@docker-compose exec postgres psql -U clara -d clara

psql-analytics:
	@docker-compose exec timescaledb psql -U clara -d clara_analytics

# Backup
backup:
	@echo "💾 Creating backups..."
	@mkdir -p backups
	@echo "📦 Backing up Redis..."
	@docker-compose exec redis redis-cli SAVE
	@docker cp clara-redis:/data/dump.rdb ./backups/redis-$$(date +%Y%m%d-%H%M%S).rdb
	@echo "📦 Backing up PostgreSQL..."
	@docker-compose exec postgres pg_dump -U clara clara > backups/clara-$$(date +%Y%m%d-%H%M%S).sql
	@echo "📦 Backing up TimescaleDB..."
	@docker-compose exec timescaledb pg_dump -U clara clara_analytics > backups/analytics-$$(date +%Y%m%d-%H%M%S).sql
	@echo "✅ Backups created in ./backups/"
	@ls -lh backups/ | tail -3

# Cleanup
clean:
	@echo "🧹 Cleaning up (preserving data)..."
	@docker-compose down
	@echo "✅ Containers removed, data preserved in volumes"

clean-all:
	@echo "⚠️  WARNING: This will delete ALL data!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "🗑️  Removing everything..."
	@docker-compose down -v
	@echo "✅ All containers and data removed"

reset: clean-all
	@echo "🔄 Resetting and restarting..."
	@make setup
	@echo "✅ Reset complete!"

# Development helpers
dev-status:
	@echo "📊 Clara Infrastructure Status"
	@echo ""
	@echo "Services:"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Redis Stats:"
	@docker-compose exec redis redis-cli INFO stats | grep -E "total_connections_received|total_commands_processed|keyspace"
	@echo ""
	@echo "PostgreSQL Stats:"
	@docker-compose exec postgres psql -U clara -d clara -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 5;"

# Quick tests
test-connections:
	@echo "🧪 Testing connections..."
	@echo -n "Redis: "
	@docker-compose exec redis redis-cli ping || echo "❌ FAILED"
	@echo -n "PostgreSQL: "
	@docker-compose exec postgres pg_isready -U clara || echo "❌ FAILED"
	@echo -n "TimescaleDB: "
	@docker-compose exec timescaledb pg_isready -U clara || echo "❌ FAILED"
	@echo "✅ Connection tests complete"

# Initialize schemas (if needed)
init-schemas:
	@echo "📝 Initializing database schemas..."
	@docker-compose exec postgres psql -U clara -d clara < init-scripts/01-init-schema.sql
	@docker-compose exec timescaledb psql -U clara -d clara_analytics < init-scripts-timescale/01-init-timescale.sql
	@echo "✅ Schemas initialized"
