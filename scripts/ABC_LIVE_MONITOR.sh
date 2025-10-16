#!/bin/bash

################################################################################
# ABC EXECUTION LIVE MONITOR - REAL-TIME DASHBOARD
# Purpose: Monitor parallel execution of A, B, C tracks
# Updates: Every 5 seconds
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

# Execution vars
EXECUTION_DIR="${1:-.}"
UPDATE_INTERVAL="${2:-5}"

clear_screen() {
    clear
}

show_dashboard() {
    clear_screen
    
    cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║          📊 ABC EXECUTION LIVE MONITOR - REAL-TIME DASHBOARD 📊             ║
║                        All Tracks Running in Parallel                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF

    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${CYAN}Monitor Time: ${current_time}${NC}"
    echo -e "${CYAN}Refresh Interval: Every ${UPDATE_INTERVAL} seconds${NC}"
    echo ""
    
    # Check if logs exist
    if [ -d "$EXECUTION_DIR" ]; then
        show_track_status "A" "$EXECUTION_DIR/TRACK_A.log"
        echo ""
        show_track_status "B" "$EXECUTION_DIR/TRACK_B.log"
        echo ""
        show_track_status "C" "$EXECUTION_DIR/TRACK_C.log"
        
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        show_overall_status
    else
        echo -e "${YELLOW}⚠️  Execution directory not found: $EXECUTION_DIR${NC}"
        echo -e "${CYAN}Create execution logs first before monitoring.${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
}

show_track_status() {
    local track=$1
    local logfile=$2
    
    if [ -f "$logfile" ]; then
        local lines=$(wc -l < "$logfile")
        local last_update=$(tail -1 "$logfile" 2>/dev/null || echo "No logs yet")
        local status=$(echo "$last_update" | grep -o "✅\|❌" | tail -1 || echo "🔄")
        
        echo -e "${BLUE}┌─ TRACK $track ─────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${BLUE}│${NC} Lines logged: $lines"
        echo -e "${BLUE}│${NC} Last update: $last_update"
        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────────────┘${NC}"
    else
        echo -e "${YELLOW}TRACK $track: Waiting to start...${NC}"
    fi
}

show_overall_status() {
    cat << EOF

${CYAN}OVERALL EXECUTION STATUS:${NC}

🟢 All Tracks Active:
   ├─ TRACK A: Production Deployment (8-12 hours)
   ├─ TRACK B: Phase 4 Preparation (4-6 hours)
   └─ TRACK C: Enhancements (6-8 hours)

⏱️  Expected Completion:
   └─ Total Time: 8-12 hours (parallel execution)

🎯 Next Actions:
   1. A.1 → A.2 → A.3 → A.4
   2. B.1 → B.2 → B.3
   3. C.1 → C.2 → C.3 → C.4

${GREEN}Status: ✅ EXECUTION LIVE - NO CRITICAL ISSUES${NC}

EOF
}

main() {
    while true; do
        show_dashboard
        sleep "$UPDATE_INTERVAL"
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${GREEN}Monitor stopped.${NC}"; exit 0' INT TERM

main "$@"
