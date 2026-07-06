FUNNEL_SQL = """
WITH funnel AS (
    SELECT
        event_name,
        COUNT(DISTINCT organization_id) AS organizations
    FROM events
    WHERE event_name IN (
        'signed_up',
        'created_workspace',
        'invited_teammate',
        'connected_integration',
        'created_project',
        'exported_report',
        'viewed_pricing',
        'started_checkout',
        'upgraded_to_paid'
    )
    GROUP BY event_name
)
SELECT
    event_name,
    organizations,
    ROUND(100.0 * organizations / MAX(organizations) OVER (), 1) AS pct_of_signups
FROM funnel
ORDER BY CASE event_name
    WHEN 'signed_up' THEN 1
    WHEN 'created_workspace' THEN 2
    WHEN 'invited_teammate' THEN 3
    WHEN 'connected_integration' THEN 4
    WHEN 'created_project' THEN 5
    WHEN 'exported_report' THEN 6
    WHEN 'viewed_pricing' THEN 7
    WHEN 'started_checkout' THEN 8
    WHEN 'upgraded_to_paid' THEN 9
END
"""

COHORT_SQL = """
SELECT
    o.segment,
    strftime('%Y-%m', u.signup_date) AS signup_month,
    COUNT(DISTINCT o.id) AS trials,
    SUM(CASE WHEN s.status = 'paid' THEN 1 ELSE 0 END) AS paid_customers,
    ROUND(100.0 * SUM(CASE WHEN s.status = 'paid' THEN 1 ELSE 0 END) / COUNT(DISTINCT o.id), 1) AS conversion_rate
FROM organizations o
JOIN users u ON u.organization_id = o.id
JOIN subscriptions s ON s.organization_id = o.id
GROUP BY o.segment, signup_month
ORDER BY signup_month, o.segment
"""

FEATURE_USAGE_SQL = """
SELECT
    fu.feature_name,
    ROUND(AVG(CASE WHEN s.status = 'paid' THEN fu.usage_count END), 2) AS avg_paid_usage,
    ROUND(AVG(CASE WHEN s.status != 'paid' THEN fu.usage_count END), 2) AS avg_unpaid_usage,
    ROUND(
        AVG(CASE WHEN s.status = 'paid' THEN fu.usage_count END) -
        AVG(CASE WHEN s.status != 'paid' THEN fu.usage_count END),
        2
    ) AS usage_gap
FROM feature_usage fu
JOIN subscriptions s ON s.organization_id = fu.organization_id
GROUP BY fu.feature_name
ORDER BY usage_gap DESC
"""

MONETIZATION_SQL = """
SELECT
    p.name AS plan_name,
    COUNT(DISTINCT s.organization_id) AS trials,
    SUM(CASE WHEN s.status = 'paid' THEN 1 ELSE 0 END) AS paid_customers,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM events e
        WHERE e.organization_id = s.organization_id
        AND e.event_name = 'viewed_pricing'
    ) THEN 1 ELSE 0 END) AS viewed_pricing,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM events e
        WHERE e.organization_id = s.organization_id
        AND e.event_name = 'started_checkout'
    ) THEN 1 ELSE 0 END) AS started_checkout,
    ROUND(100.0 * SUM(CASE WHEN s.status = 'paid' THEN 1 ELSE 0 END) / COUNT(DISTINCT s.organization_id), 1) AS conversion_rate
FROM subscriptions s
JOIN plans p ON p.id = s.plan_id
GROUP BY p.name
ORDER BY conversion_rate DESC
"""

EXPERIMENT_SQL = """
SELECT
    name,
    hypothesis,
    target_segment,
    status,
    metric
FROM experiments
ORDER BY status, target_segment
"""
