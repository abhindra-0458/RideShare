-- Initial database setup script

-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create enum types
CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE ride_status AS ENUM ('scheduled', 'active', 'completed', 'cancelled');
CREATE TYPE ride_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE participant_status AS ENUM ('pending', 'accepted', 'rejected');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    bio TEXT,
    profile_picture_url TEXT,
    social_links JSONB DEFAULT '{}',
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_profile_visible BOOLEAN DEFAULT true,
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    last_location_update TIMESTAMP,
    refresh_token TEXT,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rides table
CREATE TABLE rides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_latitude DECIMAL(10, 8) NOT NULL,
    start_longitude DECIMAL(11, 8) NOT NULL,
    start_address VARCHAR(500) NOT NULL,
    end_latitude DECIMAL(10, 8) NOT NULL,
    end_longitude DECIMAL(11, 8) NOT NULL,
    end_address VARCHAR(500) NOT NULL,
    scheduled_date_time TIMESTAMP NOT NULL,
    is_public BOOLEAN DEFAULT true,
    max_participants INTEGER DEFAULT 10,
    estimated_duration_minutes INTEGER,
    difficulty ride_difficulty DEFAULT 'medium',
    status ride_status DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ride participants table
CREATE TABLE ride_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status participant_status DEFAULT 'pending',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ride_id, user_id)
);

-- Location updates table
CREATE TABLE location_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(8, 2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drift alerts table
CREATE TABLE drift_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    distance DECIMAL(8, 2) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_location ON users(current_latitude, current_longitude);
CREATE INDEX idx_users_last_location_update ON users(last_location_update);

CREATE INDEX idx_rides_created_by ON rides(created_by);
CREATE INDEX idx_rides_status ON rides(status);
CREATE INDEX idx_rides_public ON rides(is_public);
CREATE INDEX idx_rides_scheduled_date ON rides(scheduled_date_time);
CREATE INDEX idx_rides_start_location ON rides(start_latitude, start_longitude);
CREATE INDEX idx_rides_end_location ON rides(end_latitude, end_longitude);
CREATE INDEX idx_rides_difficulty ON rides(difficulty);

CREATE INDEX idx_ride_participants_ride_id ON ride_participants(ride_id);
CREATE INDEX idx_ride_participants_user_id ON ride_participants(user_id);
CREATE INDEX idx_ride_participants_status ON ride_participants(status);

CREATE INDEX idx_location_updates_user_id ON location_updates(user_id);
CREATE INDEX idx_location_updates_timestamp ON location_updates(timestamp);
CREATE INDEX idx_location_updates_user_timestamp ON location_updates(user_id, timestamp);

CREATE INDEX idx_drift_alerts_ride_id ON drift_alerts(ride_id);
CREATE INDEX idx_drift_alerts_user_id ON drift_alerts(user_id);
CREATE INDEX idx_drift_alerts_created_at ON drift_alerts(created_at);

-- Create geographic indexes for spatial queries
CREATE INDEX idx_users_location_gist ON users USING GIST(ST_MakePoint(current_longitude, current_latitude));
CREATE INDEX idx_rides_start_location_gist ON rides USING GIST(ST_MakePoint(start_longitude, start_latitude));
CREATE INDEX idx_rides_end_location_gist ON rides USING GIST(ST_MakePoint(end_longitude, end_latitude));

-- Create triggers to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rides_updated_at BEFORE UPDATE ON rides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample admin user (password: Admin123!)
INSERT INTO users (
    email, 
    password, 
    first_name, 
    last_name, 
    phone, 
    role,
    bio
) VALUES (
    'admin@rideshare.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKbNbxtrzXmqM0K', -- Admin123!
    'System',
    'Administrator',
    '+1234567890',
    'admin',
    'System administrator account'
);

-- Create sample data (optional)
-- INSERT INTO users (email, password, first_name, last_name, phone) VALUES
-- ('john.doe@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKbNbxtrzXmqM0K', 'John', 'Doe', '+1234567891'),
-- ('jane.smith@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKbNbxtrzXmqM0K', 'Jane', 'Smith', '+1234567892');
