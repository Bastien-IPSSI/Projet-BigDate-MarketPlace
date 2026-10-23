-- Executive Summary : CA du jour (visualisation « Tendance »)
-- {{date}} : variable Metabase de type Date, facultative.
--   - vide       : « le jour » = la dernière date chargée par le pipeline
--   - renseignée : « le jour » = cette date (ou la dernière date chargée avant elle)
-- [[ ... ]] : Metabase n'inclut ce morceau que si la variable est renseignée.
-- Metabase affiche la dernière valeur et l'évolution par rapport à la veille.
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT dt AS "Date", revenue AS "CA"
FROM analytics.daily_summary, ref
WHERE dt > ref.d - 7 AND dt <= ref.d
ORDER BY dt;
