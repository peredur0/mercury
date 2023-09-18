SELECT mc.mot, SUM(md.occurrence) as occurrence
FROM mots_document as md
JOIN mot_corpus as mc ON mc.id_mot = md.id_mot
JOIN messages as me ON md.id_message = me.id_message
JOIN categories as ca ON me.id_cat = ca.id_cat
WHERE ca.type LIKE 'spam'
GROUP BY mc.mot
ORDER BY SUM(md.occurrence) DESC
LIMIT 50;

FROM mots_document as md
JOIN mot_corpus as mc ON mc.id_mot = md.id_mot
JOIN messages as me ON md.id_message = me.id_message
JOIN categories as ca ON me.id_cat = ca.id_cat
WHERE ca.type LIKE 'ham'
GROUP BY mc.mot
ORDER BY SUM(md.occurrence) DESC
LIMIT 50;

SELECT ca.type, nl.success, COUNT(nl.id_message), nl.raison
FROM nlp_status as nl
JOIN messages as me ON me.id_message = nl.id_message
JOIN categories as ca ON me.id_cat = ca.id_cat
WHERE nl.success = false GROUP BY ca.type, nl.success, nl.raison;


# regarder les 50 mots avec le plus et me moins occurrence et le plus de fréquence dans les hams
# et dans les spam.
