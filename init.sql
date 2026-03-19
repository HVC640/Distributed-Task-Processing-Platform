CREATE TABLE IF NOT EXISTS tasks
(
    task_id uuid NOT NULL DEFAULT gen_random_uuid(),
    task_type character varying(100) NOT NULL,
    payload jsonb,
    status character varying(50) NOT NULL,
    uploaded_by character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    scheduled_for timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    retry_count integer DEFAULT 0,
    max_retries integer DEFAULT 3,
    result jsonb,
    error_message text,
    priority character varying(100) DEFAULT 'low',    
    worker_id TEXT,
    last_heartbeat TIMESTAMP,
    lease_expires_at TIMESTAMP,

    CONSTRAINT tasks_pkey PRIMARY KEY (task_id)
);