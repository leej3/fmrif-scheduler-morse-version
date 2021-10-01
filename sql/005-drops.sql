-- this is some test code that is not referenced anywhere
drop function foof;

-- experiment from 2009 that was never cleaned up
drop table temp_timelapse;

-- all views are unnecessary or will need to be redone anyway
drop view departments;
drop view departments_agt;
drop view schedule;
drop view schedule_agt;
drop view template;
drop view vlogsched;
drop view vlogsched_auditlapse;
drop view vtblsched_audit;
drop view vtblsched_audit_alloc;
drop view vtblsched_audit_total;

-- storing the database user is not helpful, these will need to change to an fkey ref on a users table
alter table tblsched alter column chg_by drop default;
alter table tlkpresearcher alter column chg_by drop default;

-- most rules need to be redone and will be replaced by triggers
drop rule tblsched_ins on tblsched;
drop rule tblsched_updateon on tblsched;
drop rule tlkpresearcher_del on tlkpresearcher;
drop rule tlkpresearcher_ins on tlkpresearcher;
drop rule tlkpresearcher_upd on tlkpresearcher;