import React from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import Typography from "@mui/material/Typography";
import Drawer from "@mui/material/Drawer";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import CircularProgress from "@mui/material/CircularProgress";
import Close from "@mui/icons-material/Close";
// jarr
import BuildFeed from "./Feed/Build";
import AddEditFeed from "./Feed";
import AddEditCategory from "./Category";
import SettingsPanel from "./SettingsPanel";
import { closePanel } from "./slice";
import editPanelStyle from "./editPanelStyle";

const mapDispatchToProps = (dispatch) => ({
  close() {
    dispatch(closePanel());
  },
});

function mapStateToProps(state) {
  return { isOpen: state.edit.isOpen,
           isLoading: state.edit.isLoading,
           job: state.edit.job,
           objType: state.edit.objType,
  };
}

const EditPanel = ({ isOpen, isLoading, job, objType, close }) => {
  const classes = editPanelStyle();
  let form;
  if (isLoading) {
    form = <div className={classes.loadEditPanel}><CircularProgress /></div>;
  } else if (objType === "feed" && job === "add") {
    form = <BuildFeed isLoading={isLoading} />;
  } else if (objType === "feed") {
    form = <AddEditFeed job={job} />;
  } else if (objType === "category") {
    form = <AddEditCategory job={job} />;
  } else if (objType === "user") {
    form = <SettingsPanel />;
  }
  return (
    <Drawer
      variant="persistent"
      anchor="right"
      open={isOpen}
      className={classes.editPanel}
      classes={{
        paper: classes.editPanelPaper,
      }}
    >
      <div className={classes.editPanelHeaderSticky}>
        <div className={classes.editPanelHeader}>
          <IconButton onClick={close}>
            <Close />
          </IconButton>
          <Typography className={classes.editPanelTitle}>
            {job.charAt(0).toUpperCase()}{job.slice(1)}ing {objType.charAt(0).toUpperCase()}{objType.slice(1)}
          </Typography>
        </div>
      </div>
      <Divider />
      <div className={classes.editPanelForm}>
        {form}
      </div>
    </Drawer>
  );
};

EditPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  isLoading: PropTypes.bool.isRequired,
  job: PropTypes.string,
  objType: PropTypes.string,
  close: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(EditPanel);
