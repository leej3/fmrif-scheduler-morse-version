comment on table tlogsched is 'Logged changes from tblsched';

create function log_sched_changes_impl() returns trigger as $$
	begin
		if(TG_OP = 'UPDATE') then
			insert into tlogsched (
				schedid,
				scannercode, scheddate, schedhour, deptcode, researchercode, time_used,
				scannercode_old, scheddate_old, schedhour_old, deptcode_old, researchercode_old, time_used_old,
				chg_at, chg_by
			) values (
				NEW.schedid,
				NEW.scannercode, NEW.scheddate, NEW.schedhour, NEW.deptcode, NEW.researchercode, NEW.time_used,
				OLD.scannercode, OLD.scheddate, OLD.schedhour, OLD.deptcode, OLD.researchercode, OLD.time_used,
				NEW.chg_at, NEW.chg_by
			);
			return NEW;
		elseif(TG_OP = 'DELETE') then
			insert into tlogsched (
				schedid,
				scannercode, scheddate, schedhour, -- need these for reference, but leave rest of new values null as they're gone
				scannercode_old, scheddate_old, schedhour_old, deptcode_old, researchercode_old, time_used_old
			) values (
				OLD.schedid,
				OLD.scannercode, OLD.scheddate, OLD.schedhour, -- keep these to relate the entry back
				OLD.scannercode, OLD.scheddate, OLD.schedhour, OLD.deptcode, OLD.researchercode, OLD.time_used
			);
			return OLD;
		elseif(TG_OP = 'INSERT') then
			insert into tlogsched (
				schedid,
				scannercode, scheddate, schedhour, deptcode, researchercode, time_used,
				chg_at, chg_by
			) values (
				NEW.schedid,
				NEW.scannercode, NEW.scheddate, NEW.schedhour, NEW.deptcode, NEW.researchercode, NEW.time_used,
				NEW.chg_at, NEW.chg_by
			);
			return NEW;
		end if;
	end;
$$
language plpgsql;

create trigger log_sched_changes after insert or update or delete on tblsched for each row execute procedure log_sched_changes_impl();
