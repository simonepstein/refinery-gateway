from typing import Dict, Any, List, Union

from .search_enum import (
    SearchOrderBy,
    SearchColumn,
    FilterDataDictKeys,
    SearchOperators,
    SearchQueryTemplate,
    SearchTargetTables,
)
from submodules.model.enums import LabelSource


def build_search_condition_value(target: SearchOperators, value) -> str:
    if target in __lookup_operator:
        operator = __lookup_operator[target]
        if target == SearchOperators.IN:
            all_in_values = ""
            for v in value:
                part = v
                if isinstance(v, str):
                    part = "'" + part + "'"
                if all_in_values != "":
                    all_in_values += ", " + part
                else:
                    all_in_values = part
            return operator.replace("@@VALUES@@", all_in_values)
        else:
            if target not in __lookup_operator_has_quotes and isinstance(value, str):
                value = "'" + value + "'"
            return operator.replace("@@VALUE@@", value)
    else:
        raise ValueError(target.value + " no operator info")


def build_search_condition(filter_element: Dict[str, str]) -> str:
    table = SearchTargetTables[filter_element[FilterDataDictKeys.TARGET_TABLE.value]]
    column = SearchColumn[filter_element[FilterDataDictKeys.TARGET_COLUMN.value]]
    column_text = build_search_column_text(filter_element)
    operator = SearchOperators[filter_element[FilterDataDictKeys.OPERATOR.value]]

    if operator == SearchOperators.IN:
        if table == SearchTargetTables.RECORD and column == SearchColumn.DATA:
            filter_values = filter_element[FilterDataDictKeys.VALUES.value][1:]
        else:
            filter_values = filter_element[FilterDataDictKeys.VALUES.value]
        return column_text + build_search_condition_value(operator, filter_values)
    else:
        if table == SearchTargetTables.RECORD and column == SearchColumn.DATA:
            filter_value = filter_element[FilterDataDictKeys.VALUES.value][1]
        else:
            filter_value = filter_element[FilterDataDictKeys.VALUES.value][0]

        return column_text + build_search_condition_value(operator, filter_value)


def build_search_column_text(filter_element: Dict[str, str]) -> str:

    table = SearchTargetTables[filter_element[FilterDataDictKeys.TARGET_TABLE.value]]
    table_alias = __lookup_table_alias[table]
    column = SearchColumn[filter_element[FilterDataDictKeys.TARGET_COLUMN.value]]

    if table == SearchTargetTables.RECORD and column == SearchColumn.DATA:
        col_str = f"{table_alias}.\"data\" ->> '{filter_element[FilterDataDictKeys.VALUES.value][0]}'::TEXT"
    else:
        col_str = f"{table_alias}.{column.value}"
    return col_str


def build_order_column_record_data(order_by_col_text: str, data_type: str) -> str:
    json_field = order_by_col_text.split("@")[1]

    text = f"r.\"data\" ->> '{json_field}'"
    if data_type == "INTEGER" or data_type == "FLOAT":
        text = f"CAST({text} AS {data_type})"

    text += f' "order_{json_field}"'
    return text


def build_order_by_record_data(order_by_col_text: str, direction: str) -> str:
    json_field = order_by_col_text.split("@")[1]
    text = f'"order_{json_field}"'
    if direction == "ASC":
        text = f"{text} {direction} NULLS FIRST"
    else:
        text = f"{text} {direction} NULLS LAST"
    return text


def build_order_by_column(order_by_col_text: str, direction: str) -> str:

    order_by_col = SearchOrderBy[order_by_col_text]
    column = __lookup_order_by_column[order_by_col].value

    if __lookup_order_by_table[order_by_col] == SearchTargetTables.RECORD:
        if direction == "ASC":
            text = f"r.{column} {direction} NULLS FIRST"
        else:
            text = f"r.{column} {direction} NULLS LAST"
    else:
        if direction == "ASC":
            text = f"min_{column} {direction} NULLS FIRST"
        else:
            text = f"max_{column} {direction} NULLS LAST"
    return text


def build_query_template(
    target: SearchQueryTemplate, filter_values: List[Any], project_id: str
) -> str:
    template = get_query_template(target)
    if target in [
        SearchQueryTemplate.SUBQUERY_RLA_INFORMATION_SOURCE,
        SearchQueryTemplate.SUBQUERY_RLA_LABEL,
        SearchQueryTemplate.SUBQUERY_RLA_NO_LABEL,
    ]:
        template = template.replace("@@SOURCE_TYPE@@", filter_values[0])
        in_values = ""
        for v in filter_values[1:]:
            part = v
            if isinstance(v, str):
                part = "'" + part + "'"
            if in_values != "":
                in_values += ", "
            in_values += part
        template = template.replace("@@IN_VALUES@@", in_values)
    elif target == SearchQueryTemplate.SUBQUERY_RLA_CREATED_BY:
        in_values = "'" + "', '".join(filter_values) + "'"
        template = template.replace("@@IN_VALUES@@", in_values)
    elif target in [
        SearchQueryTemplate.SUBQUERY_RLA_DIFFERENT_IS_CLASSIFICATION,
        SearchQueryTemplate.SUBQUERY_RLA_DIFFERENT_IS_EXTRACTION,
    ]:
        template = template.replace("@@LABELING_TASK_ID@@", filter_values[0])
    elif target in [
        SearchQueryTemplate.SUBQUERY_RLA_CONFIDENCE,
        SearchQueryTemplate.SUBQUERY_CALLBACK_CONFIDENCE,
    ]:
        lower, upper = filter_values
        if isinstance(lower, str):
            lower = "'" + lower + "'"
            upper = "'" + upper + "'"
        else:
            lower = str(lower)
            upper = str(upper)
        template = template.replace("@@VALUE1@@", lower)
        template = template.replace("@@VALUE2@@", upper)
    template = template.replace("@@PROJECT_ID@@", project_id)
    return template


def get_query_template(target: SearchQueryTemplate) -> str:
    if target in __lookup_query_templates:
        return __lookup_query_templates[target]
    else:
        raise ValueError(target.value + " has no query template")


def build_order_by_table_select(
    order_by_col_text: str, direction: str
) -> Union[str, Dict[str, Any]]:
    if "@" in order_by_col_text:
        order_by_col_text = order_by_col_text.split("@")[0]
    order_by = SearchOrderBy[order_by_col_text]
    if order_by in __lookup_order_by_table:
        table = __lookup_order_by_table[order_by]
    else:
        raise ValueError(order_by.value + " has no table associated to it")

    if table == SearchTargetTables.RECORD:
        return "RECORD"  # already in base record no need to join
    if table == SearchTargetTables.RECORD_LABEL_ASSOCIATION:
        column = __lookup_order_by_column[order_by].value
        col_text = ""
        alias = ""
        if column == SearchColumn.CONFIDENCE.value:
            column = f"CASE WHEN source_type IN ('{LabelSource.WEAK_SUPERVISION.value}', '{LabelSource.MODEL_CALLBACK.value}') THEN confidence ELSE null END"
            alias = "min_confidence" if direction == "ASC" else "max_confidence"
        if direction == "ASC":
            if alias == "":
                alias = f"min_{column}"
            col_text = f"min({column}) {alias}"
        else:
            if alias == "":
                alias = f"max_{column}"
            col_text = f"max({column}) {alias}"
        return {
            "TABLE": table,
            "TEMPLATE_KEY": SearchQueryTemplate.ORDER_RLA,
            "COL_TEXT": col_text,
            "SELECT_APPEND": alias,
        }
    else:
        raise ValueError(order_by.value + " cant match order table to template")


__lookup_operator = {
    SearchOperators.EQUAL: " = @@VALUE@@",
    SearchOperators.CONTAINS: " ILIKE '%@@VALUE@@%'",
    SearchOperators.BEGINS_WITH: " ILIKE '@@VALUE@@%'",
    SearchOperators.ENDS_WITH: " ILIKE '%@@VALUE@@'",
    SearchOperators.IN: " IN (@@VALUES@@)",
}

__lookup_operator_has_quotes = {
    SearchOperators.CONTAINS: True,
    SearchOperators.BEGINS_WITH: True,
    SearchOperators.ENDS_WITH: True,
}


__lookup_order_by_table = {
    SearchOrderBy.WEAK_SUPERVISION_CONFIDENCE: SearchTargetTables.RECORD_LABEL_ASSOCIATION,
    SearchOrderBy.MODEL_CALLBACK_CONFIDENCE: SearchTargetTables.RECORD_LABEL_ASSOCIATION,
    SearchOrderBy.RECORD_ID: SearchTargetTables.RECORD,
    SearchOrderBy.RECORD_CREATED_AT: SearchTargetTables.RECORD,
    SearchOrderBy.RECORD_DATA: SearchTargetTables.RECORD,
}

__lookup_order_by_column = {
    SearchOrderBy.WEAK_SUPERVISION_CONFIDENCE: SearchColumn.CONFIDENCE,
    SearchOrderBy.MODEL_CALLBACK_CONFIDENCE: SearchColumn.CONFIDENCE,
    SearchOrderBy.RECORD_ID: SearchColumn.ID,
    SearchOrderBy.RECORD_CREATED_AT: SearchColumn.CREATED_AT,
}

__lookup_table_alias = {
    SearchTargetTables.RECORD: "r",
    SearchTargetTables.RECORD_LABEL_ASSOCIATION: "rla",
}

__lookup_query_templates = {
    SearchQueryTemplate.BASE_QUERY: """
SELECT r.project_id, r.id record_id @@SELECT_ADD@@
FROM record r
@@FROM_ADD@@
WHERE r.project_id = '@@PROJECT_ID@@'
@@WHERE_ADD@@
@@ORDER_BY_ADD@@ 
""",
    SearchQueryTemplate.SUBQUERY_RLA_LABEL: """
SELECT rla.project_id pID, rla.record_id rID
FROM record_label_association rla
WHERE rla.project_id = '@@PROJECT_ID@@'
    AND rla.source_type = '@@SOURCE_TYPE@@'
    AND rla.labeling_task_label_id IN (@@IN_VALUES@@)
GROUP BY rla.project_id, rla.record_id """,
    SearchQueryTemplate.SUBQUERY_RLA_NO_LABEL: """
SELECT r.project_id pID, r.id rID
FROM record r
LEFT JOIN record_label_association rla
    ON r.project_id = rla.project_id 
    AND r.id = rla.record_id 
    AND rla.source_type = '@@SOURCE_TYPE@@'
    AND rla.labeling_task_label_id IN (@@IN_VALUES@@)
WHERE r.project_id = '@@PROJECT_ID@@' AND rla.id IS NULL """,
    SearchQueryTemplate.SUBQUERY_RLA_INFORMATION_SOURCE: """
SELECT rla.project_id pID, rla.record_id rID
FROM record_label_association rla
WHERE rla.project_id = '@@PROJECT_ID@@'
    AND rla.source_type = '@@SOURCE_TYPE@@'
    AND rla.source_id IN (@@IN_VALUES@@)
GROUP BY rla.project_id, rla.record_id """,
    SearchQueryTemplate.SUBQUERY_RLA_CREATED_BY: """
SELECT rla.project_id pID, rla.record_id rID
FROM record_label_association rla
WHERE rla.project_id = '@@PROJECT_ID@@'
    AND rla.source_type = 'MANUAL'
    AND rla.created_by IN (@@IN_VALUES@@)
GROUP BY rla.project_id, rla.record_id """,
    SearchQueryTemplate.SUBQUERY_RLA_CONFIDENCE: """
SELECT rla.project_id pID, rla.record_id rID
FROM record_label_association rla
WHERE rla.project_id = '@@PROJECT_ID@@'
    AND rla.source_type = 'WEAK_SUPERVISION'
    AND rla.confidence BETWEEN @@VALUE1@@ AND @@VALUE2@@ """,
    SearchQueryTemplate.SUBQUERY_CALLBACK_CONFIDENCE: """
SELECT rla.project_id pID, rla.record_id rID
FROM record_label_association rla
WHERE rla.project_id = '@@PROJECT_ID@@'
    AND rla.source_type = 'MODEL_CALLBACK'
    AND rla.confidence BETWEEN @@VALUE1@@ AND @@VALUE2@@ """,
    SearchQueryTemplate.ORDER_RLA: """
LEFT JOIN (
    SELECT rla.project_id pID, rla.record_id rID, @@ORDER_COLUMNS@@
    FROM record_label_association rla
    GROUP BY rla.project_id, rla.record_id ) order_rla
    ON r.project_id = order_rla.pID AND r.id = order_rla.rID """,
    SearchQueryTemplate.SUBQUERY_RLA_DIFFERENT_IS_CLASSIFICATION: """
SELECT project_id pID, record_id rID, COUNT(*) different_versions, SUM(full_count) full_count
FROM (
	SELECT rla.record_id,rla.project_id, rla.labeling_task_label_id, COUNT(*) full_count
	FROM record_label_association rla
	INNER JOIN labeling_task_label ltl
		ON rla.labeling_task_label_id = ltl.id AND rla.project_id = ltl.project_id
	WHERE rla.project_id = '@@PROJECT_ID@@' 
	AND ltl.labeling_task_id = '@@LABELING_TASK_ID@@' 
	AND rla.source_type = 'INFORMATION_SOURCE'
	AND rla.return_type = 'RETURN'
	GROUP BY rla.record_id,rla.project_id, rla.labeling_task_label_id ) base_select
GROUP BY record_id, project_id
HAVING COUNT(*) >1 """,
    SearchQueryTemplate.SUBQUERY_RLA_DIFFERENT_IS_EXTRACTION: """
SELECT project_id pID, record_id rID, COUNT(*) different_versions, SUM(full_count) full_count
FROM (
	SELECT rla.record_id,rla.project_id, rlat.label,COUNT(*) full_count
	FROM record_label_association rla
	INNER JOIN (
		SELECT rla.id, rla.labeling_task_label_id ||'-' || array_agg(rlat.token_index ORDER BY rlat.token_index)::TEXT as label
		FROM record_label_association rla
		INNER JOIN record_label_association_token rlat
			ON rla.id = rlat.record_label_association_id
		WHERE rla.project_id = '@@PROJECT_ID@@' 
			AND rla.source_type = 'INFORMATION_SOURCE'
			AND rla.return_type = 'YIELD'
		GROUP BY rla.id, rla.labeling_task_label_id
	) rlat
		ON rla.id = rlat.id
	INNER JOIN labeling_task_label ltl
		ON rla.labeling_task_label_id = ltl.id AND rla.project_id = ltl.project_id
	WHERE rla.project_id = '@@PROJECT_ID@@' 
	AND ltl.labeling_task_id = '@@LABELING_TASK_ID@@' 
	AND rla.source_type = 'INFORMATION_SOURCE'
	AND rla.return_type = 'YIELD'
	GROUP BY rla.record_id,rla.project_id, rlat.label ) base_select
GROUP BY record_id, project_id
HAVING COUNT(*) >1

""",
}
