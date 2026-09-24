export const initializeDatabase = async (database) => {
  const result = await database.getFirstAsync('PRAGMA user_version');
  const currentVersion = result?.user_version ?? 0;

  await database.execAsync('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;');

  if (currentVersion < 1) {
    await database.execAsync(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT COLLATE NOCASE NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        created_at TEXT NOT NULL
      );
      PRAGMA user_version = 1;
    `);
  }
};
