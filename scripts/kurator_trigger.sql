CREATE OR REPLACE FUNCTION eng_it.fn_sync_kurator_to_roadmap()
RETURNS trigger AS C:\Users\Artur\Documents\CRD12\scripts\kurator_trigger.sql
BEGIN
  IF NEW.status = 'APPROVED' THEN
    UPDATE eng_it.tasks
       SET status = 'done',
           last_eval_ts = now()
     WHERE task_id = (
       SELECT roadmap_task_id
       FROM eng_it.technical_specifications
       WHERE tz_id = NEW.tz_id
     );
  END IF;
  RETURN NEW;
END;
C:\Users\Artur\Documents\CRD12\scripts\kurator_trigger.sql LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_kurator_to_roadmap ON eng_it.kurator_verifications;

CREATE TRIGGER trg_kurator_to_roadmap
AFTER INSERT OR UPDATE OF status
ON eng_it.kurator_verifications
FOR EACH ROW
EXECUTE FUNCTION eng_it.fn_sync_kurator_to_roadmap();
