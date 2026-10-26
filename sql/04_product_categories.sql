-- 04_product_categories.sql
-- Revenue by product category.
--
-- IMPORTANT: this dataset has no category column. The categories below are my
-- own rough grouping, built by looking for keywords in the product
-- description with CASE WHEN. The order of the WHEN branches matters because
-- CASE stops at the first match - for example "CHRISTMAS CANDLE" is counted as
-- Christmas, not as Candles & Lighting.
--
-- Roughly 15% of revenue does not match any keyword and lands in "Other", so
-- this is a useful summary rather than an exact category report. I say the
-- same thing in the write-up.

WITH categorised AS (
    SELECT
        invoice,
        quantity,
        revenue,
        CASE
            WHEN description LIKE '%CHRISTMAS%' OR description LIKE '%XMAS%'
              OR description LIKE '%ADVENT%'    OR description LIKE '%SANTA%'
              OR description LIKE '%EASTER%'    OR description LIKE '%HALLOWEEN%'
                THEN 'Christmas & Seasonal'
            WHEN description LIKE '%BAG%'     OR description LIKE '%TOTE%'
              OR description LIKE '%SHOPPER%' OR description LIKE '%SATCHEL%'
              OR description LIKE '%RUCKSACK%'
                THEN 'Bags'
            WHEN description LIKE '%T-LIGHT%' OR description LIKE '%CANDLE%'
              OR description LIKE '%LANTERN%' OR description LIKE '%LIGHT%'
              OR description LIKE '%LAMP%'
                THEN 'Candles & Lighting'
            WHEN description LIKE '%CAKE%'   OR description LIKE '%BAKING%'
              OR description LIKE '%MUG%'    OR description LIKE '%TEAPOT%'
              OR description LIKE '%JUG%'    OR description LIKE '%BOWL%'
              OR description LIKE '%PLATE%'  OR description LIKE '%CUTLERY%'
              OR description LIKE '%APRON%'  OR description LIKE '%BOTTLE%'
              OR description LIKE '%KITCHEN%' OR description LIKE '%TRAY%'
              OR description LIKE '%SPOON%'  OR description LIKE '%BISCUIT%'
              OR description LIKE '%CHOCOLATE%' OR description LIKE '%CUP%'
                THEN 'Kitchen & Baking'
            WHEN description LIKE '%BOX%'     OR description LIKE '%STORAGE%'
              OR description LIKE '%JAR%'     OR description LIKE '%BASKET%'
              OR description LIKE '%CRATE%'   OR description LIKE '%HOLDER%'
              OR description LIKE '%DRAWER%'  OR description LIKE '%CABINET%'
                THEN 'Storage & Boxes'
            WHEN description LIKE '%CARD%'    OR description LIKE '%WRAP%'
              OR description LIKE '%PAPER%'   OR description LIKE '%NAPKIN%'
              OR description LIKE '%BUNTING%' OR description LIKE '%PARTY%'
              OR description LIKE '%BALLOON%' OR description LIKE '%DOILY%'
                THEN 'Paper & Party'
            WHEN description LIKE '%HEART%'   OR description LIKE '%FRAME%'
              OR description LIKE '%MIRROR%'  OR description LIKE '%CUSHION%'
              OR description LIKE '%CLOCK%'   OR description LIKE '%SIGN%'
              OR description LIKE '%HANGING%' OR description LIKE '%WREATH%'
              OR description LIKE '%DECORATION%' OR description LIKE '%ORNAMENT%'
              OR description LIKE '%VASE%'    OR description LIKE '%HOOK%'
              OR description LIKE '%GARLAND%' OR description LIKE '%PHOTO%'
                THEN 'Home Decor'
            WHEN description LIKE '%NECKLACE%' OR description LIKE '%BRACELET%'
              OR description LIKE '%EARRING%'  OR description LIKE '%BEAD%'
              OR description LIKE '%SCARF%'    OR description LIKE '%PURSE%'
              OR description LIKE '%UMBRELLA%' OR description LIKE '%HAIR%'
                THEN 'Jewellery & Accessories'
            WHEN description LIKE '%TOY%'    OR description LIKE '%GAME%'
              OR description LIKE '%PUZZLE%' OR description LIKE '%DOLL%'
              OR description LIKE '%CRAFT%'  OR description LIKE '%STICKER%'
              OR description LIKE '%SKITTLE%' OR description LIKE '%TEDDY%'
              OR description LIKE '%CHILDREN%'
                THEN 'Toys & Games'
            WHEN description LIKE '%GARDEN%' OR description LIKE '%PLANT%'
              OR description LIKE '%FLOWER%' OR description LIKE '%WATERING%'
              OR description LIKE '%BIRD%'   OR description LIKE '%DOORMAT%'
                THEN 'Garden & Outdoor'
            ELSE 'Other'
        END AS category
    FROM sales
)
SELECT
    category,
    COUNT(*)                                            AS transaction_lines,
    COUNT(DISTINCT invoice)                             AS orders,
    SUM(quantity)                                       AS units_sold,
    ROUND(SUM(revenue), 2)                              AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS share_of_revenue_pct
FROM categorised
GROUP BY category
ORDER BY revenue DESC;
