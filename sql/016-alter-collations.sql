-- add locale aware collation to the minority of columns that contain prose

alter table tbltemplates alter column comments type text collate "en-US-x-icu";

alter table tlkpdept alter column dept type varchar(75) collate "en-US-x-icu";

alter table tlkpscanner alter column descrip type text collate "en-US-x-icu";
