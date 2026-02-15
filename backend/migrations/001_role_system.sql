-- Role System Migration: admin/staff → god/gm/player
-- Run this BEFORE restarting the backend with the new code
-- =====================================================

-- Step 1: Create the new enum type
CREATE TYPE userrole_new AS ENUM ('god', 'gm', 'player');

-- Step 2: Alter the column to use the new enum
ALTER TABLE users 
  ALTER COLUMN role TYPE userrole_new 
  USING (
    CASE role::text
      WHEN 'admin' THEN 'god'::userrole_new
      WHEN 'staff' THEN 'player'::userrole_new
    END
  );

-- Step 3: Set the default
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'player'::userrole_new;

-- Step 4: Drop old enum and rename new one
DROP TYPE IF EXISTS userrole;
ALTER TYPE userrole_new RENAME TO userrole;

-- Verify
SELECT role, COUNT(*) FROM users GROUP BY role;
