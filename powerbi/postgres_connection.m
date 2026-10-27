// Paste into Power BI Desktop → Blank query → Advanced Editor
// Then expand the "public" schema and select the UrbanCart tables.
// Server/database can be changed for your machine.

let
    Source = PostgreSQL.Database("localhost", "urbancart")
in
    Source
