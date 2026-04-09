tmux new-session -d -s hospital

tmux send-keys -t hospital 'bash -c "source .venv/bin/activate; python app.py; exec bash"' C-m

tmux split-window -h -t hospital
tmux send-keys -t hospital 'bash -c "source .venv/bin/activate; redis-server; exec bash"' C-m

tmux split-window -v -t hospital
tmux send-keys -t hospital 'bash -c "source .venv/bin/activate; celery -A celery_app.celery_app worker --loglevel=info; exec bash"' C-m


tmux split-window -v -t hospital
tmux send-keys -t hospital 'bash -c "source .venv/bin/activate; celery -A celery_app.celery_app beat --loglevel=info; exec bash"' C-m

tmux attach -t hospital
