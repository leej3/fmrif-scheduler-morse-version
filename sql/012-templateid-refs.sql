
alter table tblsched add constraint tblsched_templateid_fkey foreign key(templateid) references tbltemplate(templateid) on delete set null;
