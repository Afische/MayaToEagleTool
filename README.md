# MayaToEagleTool
Tool that Renders Maya files from the command line and pushes them to Eagle.cool image library software

The user selects a folder and maya will iterate through all subfolders and render out .ma files from the command line without opening Maya's GUI.
It will duplicate the object in the scene and rotate it depending on what camera angles are desired in Google Sheets. It will also render with an orthographic camera that will frame these objects by getting their bounding box values.
These renders will have json data which will be used to push to Eagle.cool art organization software.
