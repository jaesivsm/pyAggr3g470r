import React, { useState } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
// material ui components
import Alert from "@mui/material/Alert";
import Fab from "@mui/material/Fab";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
// material icons
import HelpIcon from "@mui/icons-material/Help";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PlusIcon from "@mui/icons-material/Add";
// jarr
import editPanelStyle from "../../editPanelStyle";
import style from "./style";
import FilterSettingLine from "./Line";
import { addFilter } from "../../slice";

export const mapStateToProps = (state) => {
  return { filters: (state.edit.loadedObj.filters
                     ? state.edit.loadedObj.filters
                     : []).map((filter) => filter.id),
  };
};

const mapDispatchToProps = (dispatch) => ({
  add() {
    dispatch(addFilter());
  },
});

const FilterSettings = ({ filters, add }) => {
  const filterClasses = style();
  const classes = editPanelStyle();
  const [showHelp, setShowHelp] = useState(false);
  let help;
  if(showHelp) {
    help = (
      <Alert>
        <p>Filters are processed in the order you place them on every new articles that will be fetched for that feed.</p>
        <p>Through filters you can modify the read, liked status, allow or forbid clustering new articles. You can also skip entierly the creation of an article match a filter.</p>
        <p>Filters are processed one after another and you can revert the filter you applied just before. For example you might want to skip every article which title contains &quot;Python&quot; and &apos;unskip&apos; every article containing &quot;Monthy&quot;. This way you would see every article mentionning &quot;Monthy Python&quot; but none about python solely.</p>
      </Alert>
    );
  }
  return (
    <Accordion className={classes.editPanelCluster} >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="panel1a-content"
        id="panel1a-header"
      >
        <Typography className={classes.heading}>Filters Settings</Typography>
      </AccordionSummary>
      <AccordionDetails className={classes.editPanelClusterSettings}>
        <IconButton onClick={() => setShowHelp(!showHelp)}
            className={classes.showHelpButton}>
          <HelpIcon />
        </IconButton>
        {help}
        {filters.map((filter, i) =>
          <FilterSettingLine
            key={filter}
            index={i}
            position={i === 0 ? "first": (i === filters.length -1 ? "last": "none")}
          />
        )}
        <div className={filterClasses.editPanelFilterAddBtn}>
          <Fab onClick={add} color="primary">
            <PlusIcon />
          </Fab>
        </div>
      </AccordionDetails>
    </Accordion>
  );
};

FilterSettings.propTypes = {
  filters: PropTypes.array.isRequired,
  add: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(FilterSettings);
