# Data Dictionary

## Raw and Processed Fields

- `price_original_currency`: Precio publicado por el marketplace en su moneda original.
- `currency`: Moneda del precio original (`USD`, `EUR`, `GBP`).
- `price_usd`: Precio convertido a USD para análisis comparables.
- `num_brawlers`: Número estimado de brawlers/personajes en la cuenta.
- `avg_brawler_level`: Nivel promedio de brawlers (acotado a 1-11).
- `total_trophies`: Total de trofeos de la cuenta.
- `rare_skins_count`: Conteo estimado de skins raros/relevantes.
- `legendary_skins_count`: Conteo de skins legendarias (actualmente 0 en extracción genérica).
- `mythic_skins_count`: Conteo de skins míticas (actualmente 0 en extracción genérica).
- `epic_skins_count`: Conteo de skins épicas (actualmente 0 en extracción genérica).
- `rare_skins_count_simple`: Duplicado de rare_skins_count para compatibilidad.
- `site_source`: Marketplace de origen (`SkyCoach`, `PlayerAuctions`, `Gamer Markt`, etc.).
- `date_scraped`: Timestamp ISO de extracción.

## Feature Engineering Fields

- `price_per_brawler`: `price_usd / num_brawlers`.
- `price_per_trophy`: `price_usd / total_trophies`.
- `trophies_per_brawler`: `total_trophies / num_brawlers`.
- `skin_density`: `rare_skins_count / num_brawlers`.
- `site_*`: One-hot encoding del marketplace de origen.

## Target

- `price_usd` se usa como variable objetivo para regresión.
