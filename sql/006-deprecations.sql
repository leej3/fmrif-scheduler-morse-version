-- previous deprecations, for a uniform comment scheme
COMMENT ON COLUMN tlkpdept.color_wkday_eve IS 'Deprecated';
COMMENT ON COLUMN tlkpdept.color_wkend_day IS 'Deprecated';
COMMENT ON COLUMN tlkpdept.color_wkend_eve IS 'Deprecated';

-- new deprecations

comment on table technicalscans is 'Deprecated';
comment on table tlogresearcher is 'Deprecated';

comment on column tlkpresearcher.lose_to is 'Deprecated';
comment on column tblsched.post_on is 'Deprecated';

-- This may be revivived in the future but is deprecated for now;
comment on column tblsched.billdeptcode is 'Deprecated';