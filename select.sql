with counted as (
    select
        user_id,
        count(user_id) as cnt
    from
        event_log
    where
        event_timestamp >= unix_timestamp('2020-09-01 00:00:00') and event_timestamp < unix_timestamp('2020-10-01 00:00:00')
    group by
        user_id
)
select user_id from counted where cnt >= 10000 and cnt < 20000;