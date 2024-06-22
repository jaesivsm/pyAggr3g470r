import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
// material components
import Alert from '@mui/material/Alert';
import Switch from "@mui/material/Switch";
import Button from "@mui/material/Button";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
// jarr
import ProposedLinks from "./ProposedLinks";
import FilterSettings from "./FilterSettings";
import StateTextInput from "../common/StateTextInput";
import ClusterSettings from "../common/ClusterSettings";
import DeleteButton from "../common/DeleteButton";
import editPanelStyle from "../editPanelStyle";
import { closePanel, editLoadedObj } from "../slice";
import doCreateObj from "../../../hooks/doCreateObj";
import doEditObj from "../../../hooks/doEditObj";

const availableFeedTypes = ["classic", "json", "tumblr", "instagram",
                            "soundcloud", "reddit", "koreus", "twitter"];
const noUrlTypes = ["instagram", "soundcloud", "twitter"];

const extractFromLoadedObj = (state, key, def) => {
  if (state.edit.loadedObj && typeof(state.edit.loadedObj[key]) !== "undefined") {
      return state.edit.loadedObj[key];
  }
  return def;
};

const mapDispatchToProps = (dispatch) => ({
  commit(e, job) {
    e.preventDefault();
    if (job === "edit") {
      dispatch(doEditObj("feed"));
    } else {
      dispatch(doCreateObj("feed"));
    }
    dispatch(closePanel());
  },
  edit(key, value) {
    dispatch(editLoadedObj({ key, value }));
  },
});

const mapStateToProps = (state) => ({
  catId: extractFromLoadedObj(state, "category_id", null),
  feedType: extractFromLoadedObj(state, "feed_type", "classic"),
  sameLinkCount: extractFromLoadedObj(state, "same_link_count", 0),
  link: extractFromLoadedObj(state, "link", ""),
  feedId: extractFromLoadedObj(state, "id", null),
  active: extractFromLoadedObj(state, "status", "active") === "active",
  truncatedContent: extractFromLoadedObj(state, "truncated_content", false),
  categories: state.feeds.feedListRows.filter((row) => (
    row.type === "categ" || row.type === "all-categ")
  ).map((cat) => ({ id: cat.id, name: cat.str })),
});

const AddEditFeed = ({ job, categories, link, sameLinkCount,
                       feedId, catId, feedType, active, truncatedContent,
                       edit, commit }) => {
  const classes = editPanelStyle();
  let warning;
  if(sameLinkCount) {
    warning = (
      <Alert severity="info">
        You have already {sameLinkCount} feed with that link.
      </Alert>
    );
  } else if (!link) {
    warning = (
      <Alert severity="error">
        Provided URL doesn&apos;t look like a feed we support and we couldn&apos;t find a correct one.
      </Alert>
    );
  }

  const feedTypeHelper = (noUrlTypes.indexOf(feedType) === -1 ? null :
    <Alert severity="info">
      &quot;{feedType}&quot; type doesn&apos;t need a full url for link. Just the username will suffice.
    </Alert>
  );
  return (
    <form onSubmit={(e) => commit(e, job)}>
    <FormControl component="fieldset">
      {warning}
      <StateTextInput required label="Feed title" name="title" />
      <StateTextInput label="Feed description" name="description" />
      <StateTextInput required label="Feed link" name="link" />
      <ProposedLinks />
      <StateTextInput label="Website link" name="site_link" />
      <FormControlLabel
        control={<Switch color="primary" checked={active}
                    onChange={() => edit("status", active ? "paused" : "active")} />}
        label="Active feed" />
      <FormControlLabel
        control={<Switch color="primary" checked={truncatedContent}
                    onChange={() => edit("truncated_content", !truncatedContent)} /> }
        label="Active if this feed shows truncated content and you would like JARR to try to retrieve full articles" />
      <FormControl>
        <FormHelperText>Here you can change the category of the feed :</FormHelperText>
        <Select variant="outlined"
          value={catId ? catId : 0}
          onChange={(e) => edit("category_id", e.target.value)}
          className={classes.editPanelSelect}
        >
          {categories.map((cat) => (
            <MenuItem key={`cat-${cat.id}`} value={cat.id ? cat.id: 0}>
              {cat.id ? cat.name : "All"}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl>
        <FormHelperText>A type has been selected for that feed, but you can change it to your liking:</FormHelperText>
        <Select variant="outlined" value={feedType}
          onChange={(e) => edit("feed_type", e.target.value)}
          className={classes.editPanelSelect}
        >
          {availableFeedTypes.map((type) => (
            <MenuItem key={`item-${type}`} value={type}>{type}</MenuItem>
          ))}
        </Select>
        {feedTypeHelper}
      </FormControl>
      <FilterSettings />
      <ClusterSettings level="feed" />
      {!feedId ? <Alert>
        Your feed will be created but articles won&apos;t appear right away. It might take a little while before you see content appear. Be patient :)
      </Alert>: null}
      <div className={classes.editPanelButtons}>
        <Button className={classes.editPanelBtn}
          variant="contained" color="primary" type="submit">
          {!feedId ? "Create" : "Edit"} Feed
        </Button>
        <DeleteButton type="feed" className={classes.deletePanelBtn}/>
      </div>
    </FormControl>
    </form>
  );
};

AddEditFeed.propTypes = {
  link: PropTypes.string,
  sameLinkCount: PropTypes.number.isRequired,
  feedId: PropTypes.number,
  catId: PropTypes.number,
  feedType: PropTypes.string.isRequired,
  active: PropTypes.bool.isRequired,
  truncatedContent: PropTypes.bool.isRequired,
  job: PropTypes.string.isRequired,
  categories: PropTypes.array.isRequired,
  edit: PropTypes.func.isRequired,
  commit: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, mapDispatchToProps)(AddEditFeed);
