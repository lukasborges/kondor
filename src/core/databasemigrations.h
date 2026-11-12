#pragma once


namespace DatabaseMigrations {

bool createHistoryTable();
bool createBookmarksTable();
bool createRootFolders();
bool createFaviconsTable();
bool seedDefaultBookmarks();
bool createExtensionStorageTable();

}
