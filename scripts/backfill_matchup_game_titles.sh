#!/usr/bin/env bash
# Recalculates all Matchup records from scratch, grouped by GameTitle.
#
# Run this against any environment after merging the colt/separate-MUs branch
# to correct Matchup win counts that were previously combined across game titles.
#
# Usage:
#   ./scripts/backfill_matchup_game_titles.sh        # dev
#   ./scripts/backfill_matchup_game_titles.sh prod   # production

set -e

ENV=${1:-dev}
ENV_FILE="config/.env.${ENV}"

if [ "$ENV" = "prod" ]; then
    COMPOSE_ARGS="--env-file ${ENV_FILE} --file compose.prod.yaml"
else
    COMPOSE_ARGS="--env-file ${ENV_FILE}"
fi

echo "Recalculating matchups for all game titles (${ENV})..."

docker compose ${COMPOSE_ARGS} exec web python manage.py shell -c "
from data.models import GameTitle, Matchup
for gt in GameTitle.objects.all():
    print(f'  Updating matchups for {gt}...')
    Matchup.objects.create_or_update_matchups_table(game_title=gt)
print('Done.')
"
