import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// meterial components
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";
import Select from "@mui/material/Select";

import editPanelStyle from "../editPanelStyle";
import { editLoadedObj } from "../slice";

const clusteringConfOptions = {
    "cluster_enabled": "Allow article clustering",
    "cluster_tfidf_enabled": "Allow article clustering by analysing its content through TFIDF",
    "cluster_same_category": "Allow clustering between articles in the same category",
    "cluster_same_feed": "Allow clustering between articles inside the same feed",
    "cluster_wake_up": "Allow clustering process to unread an article previously marked as read"
};

function mapStateToProps(state) {
  const clusterOptions = {};
  Object.keys(clusteringConfOptions).forEach((opt) => {
      clusterOptions[opt] = typeof(state.edit.loadedObj[opt]) !== "undefined" ? state.edit.loadedObj[opt] : null;
});
  return { clusterOptions };
}

const mapDispatchToProps = (dispatch) => ({
  edit(e, key) {
    dispatch(editLoadedObj({key, value: e.target.value }));
  },
});

function ClusterSettings({ level, clusterOptions, edit }) {
  const classes = editPanelStyle();

  return (
    <Accordion className={classes.editPanelCluster} >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="panel1a-content"
        id="panel1a-header"
      >
        <Typography className={classes.heading}>Cluster Settings</Typography>
      </AccordionSummary>
      <AccordionDetails className={classes.editPanelClusterSettings}>
        {Object.entries(clusteringConfOptions)
               .map(([opt, label]) => (
          <FormControl key={opt} className={classes.editPanelClusterCtrl}>
            <InputLabel id={`label-${opt}`} className={classes.editPanelClusterLabel}>{label}</InputLabel>
            <Select labelId={`label-${opt}`} id={`select-${opt}`}
              className={classes.editPanelClusterSelect}
              value={`${clusterOptions[opt] === null && level === "user" ? true : clusterOptions[opt]}`}
              onChange={(e) => edit(e, opt)}>
              {level !== "user" ? <MenuItem value={null}>Default from parent</MenuItem> : null }
              <MenuItem value={true}>Activated</MenuItem>
              <MenuItem value={false}>Deactivated</MenuItem>
            </Select>
          </FormControl>
        ))}
      </AccordionDetails>
    </Accordion>
  );
}

ClusterSettings.propTypes = {
  level: PropTypes.string.isRequired,
  clusterOptions: PropTypes.shape({
    "cluster_enabled": PropTypes.bool,
    "cluster_tfidf_enabled": PropTypes.bool,
    "cluster_same_category": PropTypes.bool,
    "cluster_same_feed": PropTypes.bool,
    "cluster_wake_up": PropTypes.bool,
  }),
};

export default connect(mapStateToProps, mapDispatchToProps)(ClusterSettings);
