# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

深海掠夺者 (Deep Sea Odyssey) is a Flask-based web MUD game with PostgreSQL database and Redis caching. The game features a deep-sea adventure theme with exploration, combat, faction systems, and various gameplay mechanics.

## Key Commands

### Development & Testing
```bash
# Start the Flask development server
python3 game.py

# Run API tests  
python3 test_api.py

# Database operations (using models.py functions)
python3 -c "import models; print(models.get_player_full(1))"
```

### Database Management
```bash
# Connect to PostgreSQL database
psql -h 172.16.110.113 -p 5432 -U postgres -d deep_sea_odyssey

# Redis connection
redis-cli -h 172.16.110.113 -p 30379 -a gbq2KlOwPeVmQFRv
```

### Data Management Scripts
```bash
# Import/restore game data
python3 import_items.py
python3 restore_items.py
python3 fix_items.py
python3 add_atmosphere.py
```

## Architecture Overview

### Core Components
- **Flask Backend** (`game.py`): Main web server with RESTful API endpoints
- **Database Layer** (`models.py`): PostgreSQL ORM and data access functions  
- **Frontend** (`static/`): HTML5/JavaScript game interface
- **Game Systems**: Combat, factions, items, quests, marketplace

### Key Directories
- `static/`: Frontend HTML pages and assets
- `data/`: Game data files
- `scripts/`: Utility and management scripts

### Database Schema
- PostgreSQL database with tables for users, players, items, inventory, factions, etc.
- Redis for caching (host: 172.16.110.113, port: 30379)

### API Structure
RESTful endpoints for:
- Player management (`/api/player/*`)
- Game actions (`/api/game/*`) 
- Market/shop (`/api/shop/*`)
- Combat (`/api/combat/*`)
- Factions (`/api/faction/*`)

## Development Guidelines

### Authentication
- Uses agent-based authentication via `X-Agent-ID` header or `Authorization` Bearer token
- All API endpoints require authentication via the `require_auth` decorator

### Caching Strategy  
- Redis caching with 300-second TTL default
- Cache keys follow pattern: `cache_get/set/delete()` functions in `game.py`

### Database Operations
- Use context managers: `with get_db() as conn:` and `with get_cursor(conn) as cur:`
- All database connections auto-commit and auto-close

### Frontend Integration
- HTML pages in `static/` directory
- Shared JavaScript functions in `static/shared.js`
- Shared CSS styles in `static/shared.css`

## Common Tasks

### Adding New API Endpoints
1. Add route in `game.py` with `@app.route()`
2. Apply `@require_auth` decorator for protected endpoints
3. Use database context managers for data access
4. Return JSON responses with `jsonify()`

### Database Schema Changes
1. Update SQL in relevant scripts (`import_items.py`, etc.)
2. Test with `test_api.py`
3. Use database migration scripts if needed

### Frontend Development
1. Create/update HTML files in `static/`
2. Use shared.js for common functions
3. Follow existing CSS patterns in shared.css
4. Test API integration with existing endpoints

## Configuration

### Database Connection
```python
DB_CONFIG = {
    "host": "172.16.110.113",
    "port": 5432, 
    "user": "postgres",
    "password": "6WmfEvMqhOqlRdn3",
    "database": "deep_sea_odyssey"
}
```

### Redis Configuration
- Host: 172.16.110.113
- Port: 30379  
- Password: gbq2KlOwPeVmQFRv

## Troubleshooting

### Common Issues
- Database connection failures: Check PostgreSQL service and credentials
- Redis cache issues: Verify Redis server is running and accessible
- Authentication errors: Ensure `X-Agent-ID` header or Bearer token is provided
- Frontend API calls: Check CORS settings and endpoint URLs

### Debug Mode
- Set `app.debug = True` in `game.py` for detailed error messages
- Check Flask logs for request/response details
- Use `test_api.py` for isolated endpoint testing