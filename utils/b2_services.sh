#!/bin/bash
# B2 Robot Services Manager
# Usage: ./b2_services.sh [start|stop|restart|status]

# Core services (required for basic operation)
CORE_SERVICES=(
    "b2-hardware"
    "b2-twistmux"
    "b2-statepublisher"
    "b2-description"
    "b2-domain-bridge"
)

# Teleop services
TELEOP_SERVICES=(
    "b2-rc-teleop"
)

# Video services
VIDEO_SERVICES=(
    "b2-front-video"
    "b2-rear-video"
)

# Sensor services (may fail if hardware not connected)
SENSOR_SERVICES=(
    "b2-livox-mid360"
    "b2-realsense-d405"
    "b2-pcd-scan"
    "b2-nano"
)

# Web interface
WEB_SERVICES=(
    "b2-webserver"
)

# All services in startup order
ALL_SERVICES=(
    "${CORE_SERVICES[@]}"
    "${TELEOP_SERVICES[@]}"
    "${VIDEO_SERVICES[@]}"
    "${SENSOR_SERVICES[@]}"
    "${WEB_SERVICES[@]}"
)

ACTION=${1:-status}
STOP_TIMEOUT=5  # seconds to wait before force-killing

stop_service() {
    local service=$1
    echo "  Stopping $service..."
    timeout $STOP_TIMEOUT sudo systemctl stop "$service" 2>/dev/null
    if [ $? -eq 124 ]; then
        echo "    Timeout, force killing $service..."
        sudo systemctl kill -s SIGKILL "$service" 2>/dev/null
    fi
}

case $ACTION in
    start)
        echo "Starting B2 services..."
        for service in "${ALL_SERVICES[@]}"; do
            echo "  Starting $service..."
            sudo systemctl start "$service" 2>/dev/null
        done
        echo "Done. Use '$0 status' to check."
        ;;
    stop)
        echo "Stopping B2 services (timeout: ${STOP_TIMEOUT}s per service)..."
        for service in "${ALL_SERVICES[@]}"; do
            stop_service "$service"
        done
        echo "Done."
        ;;
    restart)
        echo "Restarting B2 services..."
        for service in "${ALL_SERVICES[@]}"; do
            echo "  Restarting $service..."
            timeout $STOP_TIMEOUT sudo systemctl restart "$service" 2>/dev/null
        done
        echo "Done. Use '$0 status' to check."
        ;;
    status)
        echo "B2 Service Status:"
        echo "===================="
        printf "%-30s %s\n" "SERVICE" "STATUS"
        echo "--------------------"
        for service in "${ALL_SERVICES[@]}"; do
            status=$(systemctl is-active "$service" 2>/dev/null)
            if [ "$status" = "active" ]; then
                printf "%-30s \e[32m%s\e[0m\n" "$service" "$status"
            else
                printf "%-30s \e[31m%s\e[0m\n" "$service" "$status"
            fi
        done
        ;;
    start-core)
        echo "Starting core B2 services only..."
        for service in "${CORE_SERVICES[@]}"; do
            echo "  Starting $service..."
            sudo systemctl start "$service" 2>/dev/null
        done
        echo "Done."
        ;;
    *)
        echo "B2 Services Manager"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start       Start all services"
        echo "  stop        Stop all services"
        echo "  restart     Restart all services"
        echo "  status      Show status of all services (default)"
        echo "  start-core  Start only core services (hardware, twistmux, etc.)"
        ;;
esac
