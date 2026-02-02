#!/bin/bash

# 1. Run simulation job immediately to initialize DB if needed
echo "Checking database and initializing if necessary..."
python run_simulation_job.py

# 2. Start the timed job in the background
echo "Starting hourly simulation job..."
(
    # Default to 3600 seconds if not set
    INTERVAL=${SIMULATION_INTERVAL_SECONDS:-3600}
    echo "Simulation interval set to ${INTERVAL} seconds."
    
    while true; do
        sleep $INTERVAL
        echo "Running simulation job..."
        python run_simulation_job.py
    done
) &

# 3. Start the API
echo "Starting API..."
python run.py
